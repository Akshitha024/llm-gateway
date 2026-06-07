"""Types."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProviderName(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL_MOCK = "local_mock"


class CompletionRequest(BaseModel):
    tenant_id: str
    prompt: str
    max_tokens: int = Field(default=128, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0, le=2)
    preferred_provider: ProviderName | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompletionResponse(BaseModel):
    request_id: str
    tenant_id: str
    provider: ProviderName
    text: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_usd: float
    fallback_used: bool = False
    retries: int = 0


class LedgerEntry(BaseModel):
    request_id: str
    tenant_id: str
    provider: str
    timestamp: float
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: float
    success: bool
