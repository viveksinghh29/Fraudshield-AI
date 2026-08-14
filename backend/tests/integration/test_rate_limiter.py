"""
Tests for RateLimiterMiddleware.

These build a minimal real FastAPI app with the middleware attached
and drive it with httpx's ASGITransport -- genuinely exercising the
ASGI middleware stack (not just calling dispatch() directly), which is
exactly the layer where the original bug lived: exceptions raised from
middleware added via app.add_middleware() don't reach FastAPI's
@app.exception_handler decorators, something a direct unit test of
dispatch() alone would never have caught.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.rate_limiter import RateLimiterMiddleware


def _build_test_app(*, general_limit: int, auth_limit: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimiterMiddleware, general_limit=general_limit, auth_limit=auth_limit, force_enabled=True
    )

    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/some-endpoint")
    async def some_endpoint():
        return {"ok": True}

    @app.post("/api/v1/auth/login")
    async def login():
        return {"ok": True}

    return app


@pytest.fixture
async def redis_flushed():
    """Ensures each test starts with a clean rate-limit counter state."""
    import redis.asyncio as redis

    from app.core.config import get_settings

    settings = get_settings()
    client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    async for key in client.scan_iter("ratelimit:*"):
        await client.delete(key)
    yield
    async for key in client.scan_iter("ratelimit:*"):
        await client.delete(key)
    await client.aclose()


@pytest.mark.asyncio
async def test_health_endpoint_is_never_rate_limited(redis_flushed):
    app = _build_test_app(general_limit=2, auth_limit=2)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(10):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_general_endpoint_blocks_after_limit_with_429(redis_flushed):
    """
    This is the regression test for the original bug: the middleware
    previously always received redis_client=None (captured at
    create_app() time, before the lifespan ever set a real client) and
    therefore never limited anything, and after the first fix attempt,
    raised an exception that surfaced as a generic 500 instead of 429.
    """
    app = _build_test_app(general_limit=3, auth_limit=100)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i in range(3):
            response = await client.get("/api/v1/some-endpoint")
            assert response.status_code == 200, f"request {i + 1} should succeed"

        blocked_response = await client.get("/api/v1/some-endpoint")
        assert blocked_response.status_code == 429
        body = blocked_response.json()
        assert body["error"] == "rate_limit_exceeded"
        assert "retry_after_seconds" in body["details"]


@pytest.mark.asyncio
async def test_auth_endpoints_use_a_separate_stricter_bucket(redis_flushed):
    app = _build_test_app(general_limit=100, auth_limit=2)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i in range(2):
            response = await client.post("/api/v1/auth/login")
            assert response.status_code == 200, f"login attempt {i + 1} should succeed"

        blocked = await client.post("/api/v1/auth/login")
        assert blocked.status_code == 429

        # the general bucket is untouched by auth-bucket exhaustion
        general_response = await client.get("/api/v1/some-endpoint")
        assert general_response.status_code == 200


@pytest.mark.asyncio
async def test_different_users_have_independent_rate_limit_buckets(redis_flushed):
    """
    Regression test for the "keyed by user id" behavior the original
    docstring promised but never implemented -- confirms two different
    bearer tokens are tracked as separate buckets, not merged by
    shared client IP (both requests come from the same test client/IP).
    """
    import uuid

    from app.core.security import create_access_token

    app = _build_test_app(general_limit=2, auth_limit=100)
    token_a = create_access_token(user_id=uuid.uuid4(), role="analyst")
    token_b = create_access_token(user_id=uuid.uuid4(), role="analyst")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for _ in range(2):
            response = await client.get(
                "/api/v1/some-endpoint", headers={"Authorization": f"Bearer {token_a}"}
            )
            assert response.status_code == 200

        blocked = await client.get(
            "/api/v1/some-endpoint", headers={"Authorization": f"Bearer {token_a}"}
        )
        assert blocked.status_code == 429

        # token_b's bucket is independent -- must not be blocked by token_a's exhaustion
        response_b = await client.get(
            "/api/v1/some-endpoint", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert response_b.status_code == 200


@pytest.mark.asyncio
async def test_invalid_token_falls_back_to_ip_based_limiting(redis_flushed):
    app = _build_test_app(general_limit=2, auth_limit=100)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": "Bearer not-a-real-token"}
        for _ in range(2):
            response = await client.get("/api/v1/some-endpoint", headers=headers)
            assert response.status_code == 200

        blocked = await client.get("/api/v1/some-endpoint", headers=headers)
        assert blocked.status_code == 429
