"""
SQLAlchemy declarative base.

All ORM models (Phase 3) inherit from `Base`. Kept in its own module,
separate from `session.py`, so Alembic's `env.py` can import metadata
without pulling in engine/session machinery.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass
