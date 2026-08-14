"""partial unique index: only one active model version

Revision ID: a280f8e68ae7
Revises: 2bb6878dd99a
Create Date: 2026-07-10 19:34:29.593219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a280f8e68ae7'
down_revision: Union[str, None] = '2bb6878dd99a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Defense in depth: ModelVersionRepository.activate() already ensures
    # only one row is active at the service layer, but a partial unique
    # index guarantees it at the DB level even if that invariant is ever
    # bypassed (e.g. a manual UPDATE run directly against the database).
    op.execute(
        "CREATE UNIQUE INDEX ix_model_versions_single_active "
        "ON model_versions (is_active) WHERE is_active = true"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_model_versions_single_active")
