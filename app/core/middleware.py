import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.config import settings

class MetricsCollector:
    def __init__(self):
        self.total_requests = 0
        self.status_counts = {}
        self.latency_records = []

    def record(self, status_code: int, duration_ms: float):
        self.total_requests += 1
        self.status_counts[status_code] = self.status_counts.get(status_code, 0) + 1
        self.latency_records.append(duration_ms)
        if len(self.latency_records) > 1000:
            self.latency_records.pop(0)

    def get_stats(self):
        if not self.latency_records:
            return {
                "total_requests": self.total_requests,
                "status_counts": self.status_counts,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0
            }
        sorted_records = sorted(self.latency_records)
        n = len(sorted_records)
        p50 = sorted_records[int(n * 0.50)]
        p95 = sorted_records[min(int(n * 0.95), n - 1)]
        p99 = sorted_records[min(int(n * 0.99), n - 1)]
        return {
            "total_requests": self.total_requests,
            "status_counts": self.status_counts,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2)
        }

metrics_collector = MetricsCollector()

class RateLimiter:
    def __init__(self, limit_per_minute: int = 120):
        self.limit = limit_per_minute
        self.requests = {}

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        timestamps = self.requests.get(ip, [])
        timestamps = [ts for ts in timestamps if ts > minute_ago]
        if len(timestamps) >= self.limit:
            self.requests[ip] = timestamps
            return False
        timestamps.append(now)
        self.requests[ip] = timestamps
        return True

rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        client_ip = request.client.host if request.client else "unknown"

        if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi.json"):
            if not rate_limiter.is_allowed(client_ip):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Please try again later."},
                    headers={"X-Request-ID": request_id}
                )

        start_time = time.time()
        try:
            response: Response = await call_next(request)
        except Exception:
            duration = (time.time() - start_time) * 1000
            metrics_collector.record(500, duration)
            raise

        duration = (time.time() - start_time) * 1000
        metrics_collector.record(response.status_code, duration)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.2f}ms"
        return response
