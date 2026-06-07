"""Typer CLI."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from lgw.runner import run

app = typer.Typer(no_args_is_help=True, help="LLM gateway benchmark + dev server.")
console = Console()


@app.command()
def info() -> None:
    console.print("llm-gateway: see `lgw bench --help` and `lgw serve --help`.")


@app.command()
def bench(
    out_dir: Path = typer.Option(Path("runs/latest")),
    n: int = typer.Option(8_400, help="Number of requests to drive"),
    seed: int = typer.Option(17),
) -> None:
    res = run(out_dir, n_requests=n, seed=seed)
    console.print_json(
        json.dumps(
            {
                "n_ledger_entries": res["n_ledger_entries"],
                "n_successful_attempts": res["n_successful_attempts"],
                "total_cost_usd": res["total_cost_usd"],
            },
            default=str,
        )
    )


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("lgw.middleware.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
