"""Public liveness/readiness probe for Docker, load balancers, and uptime monitoring."""

from fastapi import APIRouter, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Returns service status plus a lightweight DB connectivity check.
    Does not check Redis/Celery/LLM provider — those are covered by
    `/metrics` (Phase 9) so this endpoint stays fast for LB probes.
    """
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return {
        "status": "ok",
        "service": "fraudshield-ai-backend",
        "database": db_status,
    }
