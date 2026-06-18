"""add repos.tour_json

Revision ID: 7b2c_add_tour_json
Revises: 796910624570
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7b2c_add_tour_json"
down_revision: str | None = "796910624570"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("repos", sa.Column("tour_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("repos", "tour_json")
