"""
Pytest fixtures for integration tests — real async engine/session against
the Postgres instance defined by the environment (no mocking of the DB
layer; these tests catch real SQL/mapping bugs).
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()  # each test rolls back — no cross-test pollution

    await engine.dispose()


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """
    A real httpx.AsyncClient wired directly to the actual FastAPI app
    (app.main.app) via ASGITransport -- this exercises the genuine
    request/response cycle including middleware, dependency injection,
    and the global exception handlers, not a mocked approximation of it.

    Unlike `db_session`, requests made through this client go through
    each route's own `Depends(get_db)` session, which routers commit
    explicitly -- so data written via API calls in a test is real and
    persists. `_clean_api_test_tables` (autouse) wipes the relevant
    tables before and after every test that uses this fixture so tests
    don't see each other's leftover data.
    """
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture(autouse=False)
async def clean_api_tables():
    """
    Truncates every table API-level tests can write to. Opt-in
    (not autouse) since most of the suite doesn't need it -- only
    tests using `api_client` do, and they request this fixture
    explicitly alongside it.
    """
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE predictions, fraud_explanations, chat_history, "
                "audit_logs, user_sessions, transactions, model_versions, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE predictions, fraud_explanations, chat_history, "
                "audit_logs, user_sessions, transactions, model_versions, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    await engine.dispose()
