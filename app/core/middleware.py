import logging
import time
from collections import defaultdict
from uuid import uuid4

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("vizzy_chat.middleware")


class RateLimiter:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < 60]
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.started_at = time.perf_counter()
        request.state.request_id = str(uuid4())

        # Rate limiting
        client_key = request.headers.get("X-Forwarded-For", request.client.host) if request.client else "unknown"
        if not rate_limiter.is_allowed(client_key):
            raise HTTPException(status_code=429, detail="Too many requests")

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
                "client_ip": client_key,
            },
        )
        return response
