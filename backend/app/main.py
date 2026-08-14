"""
FastAPI application factory.

Wires together middleware, exception handlers, and versioned routers.
Business logic never lives here — this module is purely composition.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.core.exceptions import FraudShieldError
from app.core.logging import configure_logging, get_logger
from app.core.rate_limiter import RateLimiterMiddleware

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks — Redis connection, model warm-load (Phase 6+)."""
    global redis_client
    try:
        import redis.asyncio as redis

        redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
        await redis_client.ping()
        logger.info("Connected to Redis at %s", settings.REDIS_HOST)
    except Exception as exc:  # pragma: no cover - Redis is optional at scaffold stage
        logger.warning("Redis unavailable at startup, continuing without it: %s", exc)
        redis_client = None

    logger.info("%s starting up in '%s' mode", settings.APP_NAME, settings.APP_ENV)
    yield
    if redis_client is not None:
        await redis_client.close()
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="GenAI-Powered Credit Card Fraud Detection & Analyst Assistant System",
        version="0.1.0",
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # ---- CORS ----
    # Explicit methods/headers rather than "*": this API only ever uses
    # GET/POST, and only ever needs Content-Type + Authorization headers.
    # Wildcards here would work too, but combined with
    # allow_credentials=True there's no reason to be looser than the API
    # surface actually requires.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ---- Rate limiting ----
    app.add_middleware(RateLimiterMiddleware)

    # ---- Request timing / access log ----
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    # ---- Domain exception handler ----
    @app.exception_handler(FraudShieldError)
    async def fraudshield_exception_handler(request: Request, exc: FraudShieldError):
        logger.error(
            "%s: %s", exc.error_code, exc.message, extra={"extra_fields": {"details": exc.details}}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

       # ---- Fallback handler for unhandled exceptions ----
    import traceback

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        print("\n" + "=" * 80)
        print("UNHANDLED EXCEPTION")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        print("=" * 80 + "\n")

        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)

        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
            },
        )

    # ---- Routers ----
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app

app = create_app()
