"""
Integration tests for AuthService — real DB, real password hashing,
real JWT. Each test rolls back via the db_session fixture.
"""

import pytest

from app.core.exceptions import AuthenticationError, ConflictError
from app.models.user import UserRole
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_then_duplicate_email_raises_conflict(db_session):
    service = AuthService(db_session)

    user = await service.register(
        email="dup-test@fraudshield.ai",
        password="Password1",
        full_name="Dup Test",
        role=UserRole.ANALYST,
    )
    assert user.email == "dup-test@fraudshield.ai"

    with pytest.raises(ConflictError):
        await service.register(
            email="dup-test@fraudshield.ai",
            password="Password1",
            full_name="Dup Test 2",
            role=UserRole.ANALYST,
        )


@pytest.mark.asyncio
async def test_login_with_wrong_password_raises_authentication_error(db_session):
    service = AuthService(db_session)
    await service.register(
        email="login-test@fraudshield.ai",
        password="Password1",
        full_name="Login Test",
        role=UserRole.ANALYST,
    )

    with pytest.raises(AuthenticationError):
        await service.login(
            email="login-test@fraudshield.ai",
            password="WrongPassword1",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )


@pytest.mark.asyncio
async def test_full_login_refresh_logout_cycle(db_session):
    service = AuthService(db_session)
    await service.register(
        email="cycle-test@fraudshield.ai",
        password="Password1",
        full_name="Cycle Test",
        role=UserRole.ANALYST,
    )

    access_token, refresh_token = await service.login(
        email="cycle-test@fraudshield.ai",
        password="Password1",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    assert access_token
    assert refresh_token

    new_access_token = await service.refresh_access_token(refresh_token)
    assert new_access_token
    assert new_access_token != access_token

    await service.logout(refresh_token)

    with pytest.raises(AuthenticationError):
        await service.refresh_access_token(refresh_token)


@pytest.mark.asyncio
async def test_login_with_deactivated_account_is_rejected(db_session):
    service = AuthService(db_session)
    user = await service.register(
        email="deactivated-test@fraudshield.ai",
        password="Password1",
        full_name="Deactivated Test",
        role=UserRole.ANALYST,
    )
    user.is_active = False
    await db_session.flush()

    with pytest.raises(AuthenticationError):
        await service.login(
            email="deactivated-test@fraudshield.ai",
            password="Password1",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
