"""Provider protocol + mock implementations for testing and CI."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Protocol

from lgw.types import CompletionRequest, ProviderName


@dataclass
class ProviderResult:
    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: float


class Provider(Protocol):
    name: ProviderName

    async def complete(self, req: CompletionRequest) -> ProviderResult: ...


@dataclass
class MockProvider:
    """Deterministic mock with configurable failure + latency injection."""

    name: ProviderName = ProviderName.LOCAL_MOCK
    failure_rate: float = 0.0
    base_latency_ms: float = 5.0
    cost_per_in_token: float = 0.5e-6
    cost_per_out_token: float = 1.5e-6
    _counter: int = field(default=0)

    async def complete(self, req: CompletionRequest) -> ProviderResult:
        self._counter += 1
        rng = random.Random(hash((req.tenant_id, req.prompt, self._counter)) & 0xFFFFFFFF)
        # Simulate latency.
        ms = self.base_latency_ms * (1.0 + 0.3 * rng.random())
        await asyncio.sleep(ms / 1000.0)
        if rng.random() < self.failure_rate:
            raise RuntimeError(f"{self.name} mock failure")
        tokens_in = max(1, len(req.prompt) // 4)
        tokens_out = min(req.max_tokens, max(1, tokens_in // 2))
        text = f"[mock-{self.name}] response to {req.prompt[:32]}..."
        cost = tokens_in * self.cost_per_in_token + tokens_out * self.cost_per_out_token
        return ProviderResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, cost_usd=cost)


def anthropic_mock(failure_rate: float = 0.0) -> MockProvider:
    return MockProvider(
        name=ProviderName.ANTHROPIC,
        failure_rate=failure_rate,
        base_latency_ms=15.0,
        cost_per_in_token=3.0e-6,
        cost_per_out_token=15.0e-6,
    )


def openai_mock(failure_rate: float = 0.0) -> MockProvider:
    return MockProvider(
        name=ProviderName.OPENAI,
        failure_rate=failure_rate,
        base_latency_ms=12.0,
        cost_per_in_token=2.5e-6,
        cost_per_out_token=10.0e-6,
    )


def local_mock(failure_rate: float = 0.0) -> MockProvider:
    return MockProvider(
        name=ProviderName.LOCAL_MOCK,
        failure_rate=failure_rate,
        base_latency_ms=2.0,
        cost_per_in_token=0.1e-6,
        cost_per_out_token=0.5e-6,
    )
