"""FastAPI integration tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from lgw.middleware.app import app, reset_gateway


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_gateway()


@pytest.mark.asyncio
async def test_healthz() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_complete_endpoint_returns_response() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.post("/v1/complete", json={"tenant_id": "t1", "prompt": "hello"})
        assert r.status_code == 200
        body = r.json()
        assert body["tenant_id"] == "t1"
        assert body["tokens_out"] > 0


@pytest.mark.asyncio
async def test_ledger_endpoint_after_request() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        await ac.post("/v1/complete", json={"tenant_id": "t1", "prompt": "hi"})
        r = await ac.get("/v1/ledger/by-tenant")
        assert r.status_code == 200
        assert "t1" in r.json()
