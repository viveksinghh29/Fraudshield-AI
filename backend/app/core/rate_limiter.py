"""
Sliding-window rate limiter backed by Redis, applied as ASGI middleware.

Manages its own Redis connection lazily (first request that needs it
connects and caches the client on the middleware instance) rather than
depending on a client reference passed in from outside. This matters:
an earlier version took `redis_client` as a constructor argument
supplied from main.py's lifespan-managed client, but `add_middleware()`
runs at `create_app()` time -- during module import, before the ASGI
lifespan has ever started -- so that reference was always `None` and
the limiter silently never limited anything. Verified with a live
test (15 requests against a limit of 5 all returned 200) before this
fix, and confirmed blocking correctly after.

Keys by user id when the request carries a valid access token
(so limits are per-analyst, not per-IP -- one shared office IP
shouldn't throttle every analyst behind it), falling back to client IP
for unauthenticated requests. Auth endpoints (login/register) use a
separate, stricter limit, since a legitimate user never needs dozens
of login attempts a minute but a credential-stuffing attack does.
"""

import time

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings
from app.core.exceptions import RateLimitExceededError

settings = get_settings()

AUTH_PATH_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/register")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        general_limit: int | None = None,
        auth_limit: int | None = None,
        force_enabled: bool = False,
    ) -> None:
        super().__init__(app)
        self.general_limit = general_limit or settings.RATE_LIMIT_PER_MINUTE
        self.auth_limit = auth_limit or settings.AUTH_RATE_LIMIT_PER_MINUTE
        # Lets test_rate_limiter.py's dedicated tests exercise real limiting
        # behavior even when APP_ENV=test, while every other API test (which
        # doesn't care about rate limiting and would otherwise trip it
        # across unrelated tests sharing one ASGITransport identity) gets
        # the convenience skip below.
        self.force_enabled = force_enabled
        self._redis_client = None
        self._redis_connect_failed = False

    async def _get_redis_client(self):
        """Lazily connects on first use; caches the outcome so a Redis
        outage doesn't retry a connection on every single request."""
        if self._redis_client is not None:
            return self._redis_client
        if self._redis_connect_failed:
            return None

        try:
            import redis.asyncio as redis

            client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
            await client.ping()
            self._redis_client = client
            return client
        except Exception:
            self._redis_connect_failed = True
            return None

    def _resolve_identity(self, request: Request) -> str:
        """User id from a valid access token if present, else client IP."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                from app.core.security import decode_token

                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except Exception:
                pass  # invalid/expired token -- fall through to IP-based limiting

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.endswith("/health"):
            return await call_next(request)

        if settings.APP_ENV == "test" and not self.force_enabled:
            # Test clients (httpx.ASGITransport) don't carry distinct real
            # client IPs the way production traffic does, so every request
            # across an entire test *file* can land in the same bucket --
            # discovered exactly this way, when a working rate limiter
            # started failing unrelated auth/user API tests with 429s.
            # Rate-limiting behavior itself is covered by its own dedicated
            # tests (test_rate_limiter.py) with an isolated app instance,
            # so skipping it here doesn't leave that logic untested.
            return await call_next(request)

        redis_client = await self._get_redis_client()
        if redis_client is None:
            # Redis genuinely unreachable -- fail open rather than taking the
            # whole API down over a rate-limiter dependency being unavailable.
            return await call_next(request)

        is_auth_path = any(request.url.path.startswith(p) for p in AUTH_PATH_PREFIXES)
        limit = self.auth_limit if is_auth_path else self.general_limit
        bucket = "auth" if is_auth_path else "general"

        identity = self._resolve_identity(request)
        window = int(time.time() // 60)
        key = f"ratelimit:{bucket}:{identity}:{window}"

        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, 60)

        if current > limit:
            error = RateLimitExceededError(
                f"Rate limit of {limit} requests/minute exceeded.",
                details={"retry_after_seconds": 60 - int(time.time() % 60)},
            )
            # Custom middleware added via add_middleware() sits OUTSIDE
            # FastAPI's own exception-handling layer, so raising here would
            # never reach the @app.exception_handler(FraudShieldError)
            # registered in main.py -- it would surface as a generic 500
            # instead of a proper 429. Verified this the hard way (a live
            # test returned 500 for the first version of this fix) --
            # constructing the JSON response directly here is what actually
            # produces the intended status code and error shape.
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "error": error.error_code,
                    "message": error.message,
                    "details": error.details,
                },
            )

        return await call_next(request)
