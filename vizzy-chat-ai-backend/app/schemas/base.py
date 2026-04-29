from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: Any | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorInfo | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float
    provider: str
