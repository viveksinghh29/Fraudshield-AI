"""
Shared FastAPI dependencies — DB session injection (already in db/session.py),
current-user resolution from JWT, and role-based access guards.

Routers depend on `require_role(...)` rather than checking `user.role`
manually, so RBAC rules are declared once, at the route signature,
and stay consistent across the whole API surface.
"""

import uuid

import jwt
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


async def get_bearer_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing or malformed Authorization header.")
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid access token.") from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise AuthenticationError("Token is not an access token.")

    user_repo = UserRepository(db)
    user = await user_repo.get(uuid.UUID(payload["sub"]))
    if user is None:
        raise AuthenticationError("User for this token no longer exists.")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    return user


def require_role(*allowed_roles: UserRole):
    """
    Usage: `user: User = Depends(require_role(UserRole.ADMIN))`
    Raises AuthorizationError (403) if the current user's role isn't
    in `allowed_roles`. `require_role()` with no args just requires
    any authenticated, active user (equivalent to `get_current_user`).
    """

    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if allowed_roles and current_user.role not in allowed_roles:
            raise AuthorizationError(
                f"This action requires one of roles: {[r.value for r in allowed_roles]}."
            )
        return current_user

    return dependency
