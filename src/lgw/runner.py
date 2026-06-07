"""End-to-end runner: drives the gateway with 10k+ synthetic requests."""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path

from lgw.ledger.store import aggregate_by_provider, aggregate_by_tenant
from lgw.providers.base import anthropic_mock, local_mock, openai_mock
from lgw.router.gateway import Gateway
from lgw.types import CompletionRequest, ProviderName
from lgw.viz.charts import (
    cost_over_time,
    latency_by_provider_box,
    latency_hist,
    per_provider_bars,
    per_tenant_bars,
    success_rate_pie,
)


async def _drive(gw: Gateway, n: int, seed: int) -> None:
    rng = random.Random(seed)
    tenants = [f"t-{i:02d}" for i in range(8)]

    async def one(i: int) -> None:
        await gw.complete(
            CompletionRequest(
                tenant_id=rng.choice(tenants),
                prompt=f"request {i}: " + "x" * rng.randint(100, 400),
                max_tokens=rng.choice([64, 128, 256]),
            )
        )

    # Fire all requests with bounded concurrency.
    sem = asyncio.Semaphore(50)

    async def bounded(i: int) -> None:
        async with sem:
            import contextlib

            with contextlib.suppress(RuntimeError):
                await one(i)

    await asyncio.gather(*(bounded(i) for i in range(n)))


def run(out_dir: Path, n_requests: int = 10_000, seed: int = 17) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    figs = Path("results/figures")
    gw = Gateway(
        providers={
            ProviderName.LOCAL_MOCK: local_mock(failure_rate=0.0),
            ProviderName.OPENAI: openai_mock(failure_rate=0.08),
            ProviderName.ANTHROPIC: anthropic_mock(failure_rate=0.06),
        },
        preference_order=[ProviderName.LOCAL_MOCK, ProviderName.OPENAI, ProviderName.ANTHROPIC],
        max_retries=2,
    )
    asyncio.run(_drive(gw, n_requests, seed))
    by_tenant = aggregate_by_tenant(gw.ledger)
    by_provider = aggregate_by_provider(gw.ledger)
    latency_hist(gw.ledger, figs / "latency_hist.png")
    per_provider_bars(gw.ledger, figs / "per_provider.png")
    cost_over_time(gw.ledger, figs / "cost_over_time.png")
    per_tenant_bars(by_tenant, figs / "per_tenant.png")
    success_rate_pie(gw.ledger, figs / "success_rate.png")
    latency_by_provider_box(gw.ledger, figs / "latency_by_provider.png")

    success = sum(1 for e in gw.ledger if e.success)
    total_cost = sum(e.cost_usd for e in gw.ledger)
    summary: dict[str, object] = {
        "n_requests_attempted": n_requests,
        "n_ledger_entries": len(gw.ledger),
        "n_successful_attempts": success,
        "total_cost_usd": total_cost,
        "by_tenant": by_tenant,
        "by_provider": by_provider,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary
