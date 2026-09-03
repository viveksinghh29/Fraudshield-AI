"""Unit tests for app.core.security — no DB, no FastAPI, pure functions."""

import uuid

import jwt
import pytest

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_different_hash_each_time():
    h1 = hash_password("Password1")
    h2 = hash_password("Password1")
    assert h1 != h2  # bcrypt salts each hash
    assert verify_password("Password1", h1)
    assert verify_password("Password1", h2)


def test_verify_password_rejects_wrong_password():
    h = hash_password("Password1")
    assert verify_password("WrongPassword", h) is False


def test_access_token_roundtrip_contains_role_and_correct_type():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="analyst")
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.ACCESS.value
    assert payload["role"] == "analyst"


def test_refresh_token_roundtrip_has_no_role_claim():
    user_id = uuid.uuid4()
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.REFRESH.value
    assert "role" not in payload


def test_decode_token_rejects_tampered_signature():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="admin")
    tampered = token[:-4] + "abcd"

    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered)
