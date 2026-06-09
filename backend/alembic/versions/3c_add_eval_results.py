"""add eval_results table

Revision ID: 3c_add_eval_results
Revises: 2b_add_users
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = "3c_add_eval_results"
down_revision = "2b_add_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eval_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("run_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_eval_results_id", "eval_results", ["id"])


def downgrade() -> None:
    op.drop_index("ix_eval_results_id", "eval_results")
    op.drop_table("eval_results")
