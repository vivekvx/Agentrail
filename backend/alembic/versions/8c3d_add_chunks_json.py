"""add repos.chunks_json

Revision ID: 8c3d_add_chunks_json
Revises: 7b2c_add_tour_json
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8c3d_add_chunks_json"
down_revision: str | None = "7b2c_add_tour_json"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("repos", sa.Column("chunks_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("repos", "chunks_json")
