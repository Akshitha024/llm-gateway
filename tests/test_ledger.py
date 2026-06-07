"""Ledger aggregation tests."""

from __future__ import annotations

from lgw.ledger.store import aggregate_by_provider, aggregate_by_tenant
from lgw.types import LedgerEntry


def _entry(
    tenant: str, provider: str, success: bool, cost: float = 0.001, latency: float = 5.0
) -> LedgerEntry:
    return LedgerEntry(
        request_id="r",
        tenant_id=tenant,
        provider=provider,
        timestamp=0.0,
        tokens_in=10,
        tokens_out=5,
        cost_usd=cost,
        latency_ms=latency,
        success=success,
    )


def test_aggregate_by_tenant_counts_correctly() -> None:
    entries = [_entry("t1", "x", True), _entry("t1", "x", False), _entry("t2", "x", True)]
    agg = aggregate_by_tenant(entries)
    assert agg["t1"]["n_requests"] == 2
    assert agg["t1"]["n_success"] == 1
    assert agg["t1"]["n_fail"] == 1
    assert agg["t2"]["n_requests"] == 1


def test_aggregate_by_provider_sums_cost() -> None:
    entries = [_entry("t1", "openai", True, cost=0.01), _entry("t1", "openai", True, cost=0.02)]
    agg = aggregate_by_provider(entries)
    assert abs(agg["openai"]["total_cost_usd"] - 0.03) < 1e-9
