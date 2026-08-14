"""Audit log endpoint — admin-only view of the append-only audit trail."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.schemas.transaction_schema import AuditLogListResponse, AuditLogResponse

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> AuditLogListResponse:
    repo = AuditRepository(db)
    logs, total = await repo.list(
        page=page,
        page_size=page_size,
        filters={"action": action} if action else None,
        order_by=repo.model.created_at.desc(),
    )

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )
