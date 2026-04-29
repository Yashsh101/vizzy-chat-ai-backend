from datetime import datetime, timezone
import time
from typing import Any

from fastapi import Request

from app.schemas.base import APIResponse, ErrorInfo


def _latency_ms(request: Request) -> float:
    if hasattr(request.state, "latency_ms"):
        return float(request.state.latency_ms)
    started_at = getattr(request.state, "started_at", None)
    if started_at is None:
        return 0.0
    return round((time.perf_counter() - started_at) * 1000, 2)


def _metadata(request: Request, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "request_id": getattr(request.state, "request_id", None),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


def build_response(
    request: Request,
    data: Any,
    provider: str,
    metadata: dict[str, Any] | None = None,
) -> APIResponse[Any]:
    return APIResponse(
        success=True,
        data=data,
        error=None,
        metadata=_metadata(request, metadata),
        latency_ms=_latency_ms(request),
        provider=provider,
    )


def build_error_response(
    request: Request,
    provider: str,
    code: str,
    message: str,
    details: Any = None,
) -> APIResponse[None]:
    return APIResponse(
        success=False,
        data=None,
        error=ErrorInfo(code=code, message=message, details=details),
        metadata=_metadata(request),
        latency_ms=_latency_ms(request),
        provider=provider,
    )
