"""The gateway: dispatch a CompletionRequest with retry + fallback."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field

from lgw.providers.base import Provider, ProviderResult
from lgw.types import CompletionRequest, CompletionResponse, LedgerEntry, ProviderName


@dataclass
class Gateway:
    providers: dict[ProviderName, Provider]
    preference_order: list[ProviderName] = field(
        default_factory=lambda: [
            ProviderName.LOCAL_MOCK,
            ProviderName.OPENAI,
            ProviderName.ANTHROPIC,
        ]
    )
    max_retries: int = 2
    per_attempt_timeout_s: float = 5.0
    ledger: list[LedgerEntry] = field(default_factory=list)

    async def complete(self, req: CompletionRequest) -> CompletionResponse:
        rid = str(uuid.uuid4())
        order = list(self.preference_order)
        if req.preferred_provider and req.preferred_provider in self.providers:
            # Move preferred to front.
            if req.preferred_provider in order:
                order.remove(req.preferred_provider)
            order.insert(0, req.preferred_provider)

        last_error: Exception | None = None
        retries = 0
        fallback_used = False
        for i, pname in enumerate(order):
            if pname not in self.providers:
                continue
            prov = self.providers[pname]
            fallback_used = i > 0
            for attempt in range(self.max_retries + 1):
                start = time.perf_counter()
                try:
                    result: ProviderResult = await asyncio.wait_for(
                        prov.complete(req), timeout=self.per_attempt_timeout_s
                    )
                except (TimeoutError, RuntimeError) as e:
                    last_error = e
                    elapsed_ms = (time.perf_counter() - start) * 1000.0
                    self.ledger.append(
                        LedgerEntry(
                            request_id=rid,
                            tenant_id=req.tenant_id,
                            provider=pname.value,
                            timestamp=time.time(),
                            tokens_in=0,
                            tokens_out=0,
                            cost_usd=0,
                            latency_ms=elapsed_ms,
                            success=False,
                        )
                    )
                    retries += 1
                    if attempt >= self.max_retries:
                        break  # try next provider
                    await asyncio.sleep(0.01 * (attempt + 1))  # backoff
                    continue
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                self.ledger.append(
                    LedgerEntry(
                        request_id=rid,
                        tenant_id=req.tenant_id,
                        provider=pname.value,
                        timestamp=time.time(),
                        tokens_in=result.tokens_in,
                        tokens_out=result.tokens_out,
                        cost_usd=result.cost_usd,
                        latency_ms=elapsed_ms,
                        success=True,
                    )
                )
                return CompletionResponse(
                    request_id=rid,
                    tenant_id=req.tenant_id,
                    provider=pname,
                    text=result.text,
                    tokens_in=result.tokens_in,
                    tokens_out=result.tokens_out,
                    latency_ms=elapsed_ms,
                    cost_usd=result.cost_usd,
                    fallback_used=fallback_used,
                    retries=retries,
                )
            # Move on to next provider in order.
            fallback_used = i > 0
        raise RuntimeError(f"all providers failed; last error: {last_error}")
