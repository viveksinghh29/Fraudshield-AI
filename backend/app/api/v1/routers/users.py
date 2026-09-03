"""User management endpoints with authenticated access and admin-only controls."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("", response_model=list[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> list[UserResponse]:
    repo = UserRepository(db)
    users, _total = await repo.list(page=page, page_size=page_size)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_or_404(user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    repo = UserRepository(db)
    updated = await repo.update(user_id, is_active=False)
    audit_repo = AuditRepository(db)
    await audit_repo.log(
        action="USER_DEACTIVATED",
        user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
    )
    await db.commit()
    return UserResponse.model_validate(updated)


@router.post("/{user_id}/reactivate", response_model=UserResponse)
async def reactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
) -> UserResponse:
    repo = UserRepository(db)
    updated = await repo.update(user_id, is_active=True)
    audit_repo = AuditRepository(db)
    await audit_repo.log(
        action="USER_REACTIVATED",
        user_id=admin.id,
        resource_type="user",
        resource_id=user_id,
    )
    await db.commit()
    return UserResponse.model_validate(updated)
