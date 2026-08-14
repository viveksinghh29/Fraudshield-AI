"""
Unit tests for the SECRET_KEY production-safety validator in
app.core.config.Settings.

Regression coverage for a real bug found during Phase 14 hardening:
the first implementation referenced an underscore-prefixed class
attribute from inside a classmethod validator, which Pydantic's
BaseModel silently reinterprets as a private-attribute descriptor
rather than a plain constant, raising a TypeError instead of doing
the intended check. Fixed by moving the placeholder set to a module-
level constant.
"""

import os

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _make_settings(**overrides):
    env = {
        "POSTGRES_HOST": "localhost",
        **overrides,
    }
    old_environ = dict(os.environ)
    os.environ.update(env)
    try:
        return Settings()
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def test_weak_secret_key_rejected_in_production():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        _make_settings(APP_ENV="production", SECRET_KEY="weak")


def test_placeholder_secret_key_rejected_in_production():
    with pytest.raises(ValidationError, match="placeholder value"):
        _make_settings(APP_ENV="production", SECRET_KEY="CHANGE_ME_TO_A_LONG_RANDOM_SECRET")


def test_strong_secret_key_accepted_in_production():
    strong_key = "a" * 64
    settings = _make_settings(APP_ENV="production", SECRET_KEY=strong_key)
    assert settings.SECRET_KEY == strong_key


def test_weak_secret_key_accepted_in_development():
    """Dev convenience: no point forcing a 64-char secret for local iteration."""
    settings = _make_settings(APP_ENV="development", SECRET_KEY="weak")
    assert settings.SECRET_KEY == "weak"


def test_weak_secret_key_accepted_when_app_env_unset():
    """APP_ENV defaults to 'development' when not explicitly set."""
    os.environ.pop("APP_ENV", None)
    settings = _make_settings(SECRET_KEY="weak")
    assert settings.SECRET_KEY == "weak"
