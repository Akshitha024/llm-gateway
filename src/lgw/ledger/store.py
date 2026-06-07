"""Aggregate the in-memory ledger by tenant + provider."""

from __future__ import annotations

from lgw.types import LedgerEntry


def aggregate_by_tenant(entries: list[LedgerEntry]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for e in entries:
        t = out.setdefault(
            e.tenant_id,
            {
                "n_requests": 0.0,
                "n_success": 0.0,
                "n_fail": 0.0,
                "total_cost_usd": 0.0,
                "total_tokens_in": 0.0,
                "total_tokens_out": 0.0,
                "total_latency_ms": 0.0,
            },
        )
        t["n_requests"] += 1
        t["n_success"] += int(e.success)
        t["n_fail"] += int(not e.success)
        t["total_cost_usd"] += e.cost_usd
        t["total_tokens_in"] += e.tokens_in
        t["total_tokens_out"] += e.tokens_out
        t["total_latency_ms"] += e.latency_ms
    return out


def aggregate_by_provider(entries: list[LedgerEntry]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for e in entries:
        p = out.setdefault(
            e.provider,
            {
                "n_requests": 0.0,
                "n_success": 0.0,
                "total_cost_usd": 0.0,
                "total_latency_ms": 0.0,
            },
        )
        p["n_requests"] += 1
        p["n_success"] += int(e.success)
        p["total_cost_usd"] += e.cost_usd
        p["total_latency_ms"] += e.latency_ms
    return out
