"""add users table and user_id to agent_runs

Revision ID: 2b_add_users
Revises: 1a21075197c1
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = "2b_add_users"
down_revision = "1a21075197c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])
    op.add_column("agent_runs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_agent_runs_user_id", "agent_runs", "users", ["user_id"], ["id"])
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_runs_user_id", "agent_runs")
    op.drop_constraint("fk_agent_runs_user_id", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "user_id")
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_id", "users")
    op.drop_table("users")
