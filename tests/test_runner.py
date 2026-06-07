"""Runner smoke test."""

from __future__ import annotations

from pathlib import Path

from lgw.runner import run


def test_runner_small_scale(tmp_path: Path) -> None:
    s = run(tmp_path / "out", n_requests=200, seed=1)
    assert s["n_ledger_entries"] >= 200
    assert (tmp_path / "out" / "summary.json").exists()
