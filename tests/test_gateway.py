"""Gateway routing + fallback + retry tests."""

from __future__ import annotations

import pytest

from lgw.providers.base import anthropic_mock, local_mock, openai_mock
from lgw.router.gateway import Gateway
from lgw.types import CompletionRequest, ProviderName


@pytest.mark.asyncio
async def test_gateway_prefers_preference_order() -> None:
    gw = Gateway(
        providers={
            ProviderName.LOCAL_MOCK: local_mock(),
            ProviderName.OPENAI: openai_mock(),
            ProviderName.ANTHROPIC: anthropic_mock(),
        }
    )
    r = await gw.complete(CompletionRequest(tenant_id="t1", prompt="hi"))
    # First in preference order is local_mock.
    assert r.provider == ProviderName.LOCAL_MOCK
    assert not r.fallback_used


@pytest.mark.asyncio
async def test_gateway_falls_back_when_preferred_fails() -> None:
    gw = Gateway(
        providers={
            ProviderName.LOCAL_MOCK: local_mock(failure_rate=1.0),
            ProviderName.OPENAI: openai_mock(failure_rate=0.0),
        }
    )
    r = await gw.complete(CompletionRequest(tenant_id="t1", prompt="hi"))
    assert r.provider == ProviderName.OPENAI
    assert r.fallback_used


@pytest.mark.asyncio
async def test_gateway_records_ledger_entries() -> None:
    gw = Gateway(providers={ProviderName.LOCAL_MOCK: local_mock()})
    await gw.complete(CompletionRequest(tenant_id="t1", prompt="hi"))
    assert len(gw.ledger) >= 1
    assert gw.ledger[-1].success
    assert gw.ledger[-1].tenant_id == "t1"


@pytest.mark.asyncio
async def test_gateway_raises_when_all_providers_fail() -> None:
    gw = Gateway(
        providers={
            ProviderName.LOCAL_MOCK: local_mock(failure_rate=1.0),
        },
        max_retries=1,
    )
    with pytest.raises(RuntimeError, match="all providers failed"):
        await gw.complete(CompletionRequest(tenant_id="t1", prompt="hi"))


@pytest.mark.asyncio
async def test_gateway_honors_explicit_preferred() -> None:
    gw = Gateway(
        providers={
            ProviderName.LOCAL_MOCK: local_mock(),
            ProviderName.OPENAI: openai_mock(),
        }
    )
    r = await gw.complete(
        CompletionRequest(
            tenant_id="t1",
            prompt="hi",
            preferred_provider=ProviderName.OPENAI,
        )
    )
    assert r.provider == ProviderName.OPENAI
