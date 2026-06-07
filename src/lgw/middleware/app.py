"""FastAPI app exposing the gateway."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from lgw.providers.base import anthropic_mock, local_mock, openai_mock
from lgw.router.gateway import Gateway
from lgw.types import CompletionRequest, CompletionResponse, ProviderName

_gateway_singleton: Gateway | None = None


def get_gateway() -> Gateway:
    global _gateway_singleton
    if _gateway_singleton is None:
        _gateway_singleton = Gateway(
            providers={
                ProviderName.LOCAL_MOCK: local_mock(failure_rate=0.0),
                ProviderName.OPENAI: openai_mock(failure_rate=0.05),
                ProviderName.ANTHROPIC: anthropic_mock(failure_rate=0.05),
            },
            preference_order=[ProviderName.LOCAL_MOCK, ProviderName.OPENAI, ProviderName.ANTHROPIC],
        )
    return _gateway_singleton


def reset_gateway() -> None:
    global _gateway_singleton
    _gateway_singleton = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="llm-gateway", lifespan=lifespan)


@app.post("/v1/complete", response_model=CompletionResponse)
async def complete(
    req: CompletionRequest, gw: Gateway = Depends(get_gateway)
) -> CompletionResponse:
    try:
        return await gw.complete(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/ledger/by-tenant")
async def ledger_by_tenant(gw: Gateway = Depends(get_gateway)) -> dict[str, dict[str, float]]:
    from lgw.ledger.store import aggregate_by_tenant

    return aggregate_by_tenant(gw.ledger)


@app.get("/v1/ledger/by-provider")
async def ledger_by_provider(gw: Gateway = Depends(get_gateway)) -> dict[str, dict[str, float]]:
    from lgw.ledger.store import aggregate_by_provider

    return aggregate_by_provider(gw.ledger)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
