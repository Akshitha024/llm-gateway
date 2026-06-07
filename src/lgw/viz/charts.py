"""Six chart families for the gateway benchmark."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from lgw.types import LedgerEntry


def _save(fig: Figure, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)
    return out


def latency_hist(entries: list[LedgerEntry], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    arr = np.array([e.latency_ms for e in entries if e.success])
    ax.hist(arr, bins=50, color="#3b6fa1", edgecolor="white")
    ax.axvline(
        float(np.percentile(arr, 50)),
        color="#e9c46a",
        linestyle="--",
        label=f"p50={np.percentile(arr, 50):.1f}ms",
    )
    ax.axvline(
        float(np.percentile(arr, 99)),
        color="#c25a4f",
        linestyle="--",
        label=f"p99={np.percentile(arr, 99):.1f}ms",
    )
    ax.set_xlabel("latency (ms)")
    ax.set_ylabel("requests")
    ax.set_title("Request latency distribution")
    ax.legend()
    return _save(fig, out)


def per_provider_bars(entries: list[LedgerEntry], out: Path) -> Path:
    from collections import Counter

    cnt = Counter(e.provider for e in entries)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(list(cnt.keys()), list(cnt.values()), color=["#5b8d4a", "#3b6fa1", "#c25a4f"])
    ax.set_ylabel("requests served")
    ax.set_title("Requests by provider")
    return _save(fig, out)


def cost_over_time(entries: list[LedgerEntry], out: Path) -> Path:
    if not entries:
        fig, ax = plt.subplots()
        ax.axis("off")
        return _save(fig, out)
    sorted_e = sorted(entries, key=lambda e: e.timestamp)
    t0 = sorted_e[0].timestamp
    xs = [e.timestamp - t0 for e in sorted_e]
    cum = np.cumsum([e.cost_usd for e in sorted_e])
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(xs, cum * 1e3, color="#e76f51", linewidth=2)
    ax.fill_between(xs, cum * 1e3, alpha=0.2, color="#e76f51")
    ax.set_xlabel("seconds since first request")
    ax.set_ylabel("cumulative cost (USD x 1e3)")
    ax.set_title("Cost ledger over time")
    return _save(fig, out)


def per_tenant_bars(by_tenant: dict[str, dict[str, float]], out: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    tenants = sorted(by_tenant)
    cost = [by_tenant[t]["total_cost_usd"] * 1e3 for t in tenants]
    ax.bar(tenants, cost, color="#264653")
    ax.set_ylabel("total cost (USD x 1e3)")
    ax.set_title("Cost by tenant")
    return _save(fig, out)


def success_rate_pie(entries: list[LedgerEntry], out: Path) -> Path:
    s = sum(int(e.success) for e in entries)
    f = len(entries) - s
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.pie(
        [s, f],
        labels=["success", "failure (retried/fallback)"],
        autopct="%1.1f%%",
        colors=["#2a9d8f", "#c25a4f"],
    )
    ax.set_title("Per-attempt success rate")
    return _save(fig, out)


def latency_by_provider_box(entries: list[LedgerEntry], out: Path) -> Path:
    provs = sorted({e.provider for e in entries})
    data = [[e.latency_ms for e in entries if e.provider == p] for p in provs]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot(data, tick_labels=provs)
    ax.set_ylabel("latency (ms)")
    ax.set_title("Latency distribution by provider")
    return _save(fig, out)
