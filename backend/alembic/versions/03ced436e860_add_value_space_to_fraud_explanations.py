"""add value_space to fraud_explanations

Revision ID: 03ced436e860
Revises: a280f8e68ae7
Create Date: 2026-07-12 14:16:38.143887

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03ced436e860'
down_revision: Union[str, None] = 'a280f8e68ae7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: autogenerate also proposed dropping
    # 'ix_model_versions_single_active' here -- a false positive. That
    # index was created via raw op.execute() in migration a280f8e68ae7
    # (Postgres partial unique indexes aren't expressible in SQLAlchemy's
    # declarative model layer), so autogenerate's diff against the model
    # metadata can't "see" it and assumes it shouldn't exist. It's the
    # single-active-model-version safety constraint from Phase 3 and
    # must NOT be dropped -- removed from this migration deliberately.
    op.add_column(
        'fraud_explanations',
        sa.Column('value_space', sa.String(length=16), nullable=False, server_default='probability'),
    )


def downgrade() -> None:
    op.drop_column('fraud_explanations', 'value_space')
