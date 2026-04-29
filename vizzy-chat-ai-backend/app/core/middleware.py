import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("vizzy_chat.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.started_at = time.perf_counter()
        request.state.request_id = str(uuid4())

        response = await call_next(request)
        latency_ms = round((time.perf_counter() - request.state.started_at) * 1000, 2)
        request.state.latency_ms = latency_ms
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Latency-MS"] = str(latency_ms)

        logger.info(
            "Handled request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "request_id": request.state.request_id,
                "latency_ms": latency_ms,
            },
        )
        return response
