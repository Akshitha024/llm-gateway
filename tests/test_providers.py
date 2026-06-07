"""Mock provider tests."""

from __future__ import annotations

import pytest

from lgw.providers.base import anthropic_mock, local_mock, openai_mock
from lgw.types import CompletionRequest


@pytest.mark.asyncio
async def test_local_mock_completes() -> None:
    p = local_mock()
    r = await p.complete(CompletionRequest(tenant_id="t1", prompt="hello world"))
    assert r.text
    assert r.tokens_in > 0
    assert r.tokens_out > 0
    assert r.cost_usd > 0


@pytest.mark.asyncio
async def test_high_failure_rate_raises() -> None:
    p = local_mock(failure_rate=1.0)
    with pytest.raises(RuntimeError, match="mock failure"):
        await p.complete(CompletionRequest(tenant_id="t1", prompt="hi"))


@pytest.mark.asyncio
async def test_cost_monotonic_with_prompt_length() -> None:
    p = openai_mock()
    short = await p.complete(CompletionRequest(tenant_id="t1", prompt="short"))
    long = await p.complete(CompletionRequest(tenant_id="t1", prompt="x" * 400))
    assert long.cost_usd > short.cost_usd


@pytest.mark.asyncio
async def test_anthropic_more_expensive_than_local() -> None:
    anth = anthropic_mock()
    loc = local_mock()
    prompt = "x" * 200
    ar = await anth.complete(CompletionRequest(tenant_id="t1", prompt=prompt))
    lr = await loc.complete(CompletionRequest(tenant_id="t1", prompt=prompt))
    assert ar.cost_usd > lr.cost_usd
