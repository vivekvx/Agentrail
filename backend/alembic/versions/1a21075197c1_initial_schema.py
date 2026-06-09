"""initial_schema

Revision ID: 1a21075197c1
Revises:
Create Date: 2026-06-09 17:51:23.353726

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a21075197c1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repo_path', sa.String(length=2048), nullable=True),
        sa.Column('repo_url', sa.String(length=2048), nullable=True),
        sa.Column('issue_url', sa.String(length=2048), nullable=True),
        sa.Column('user_task', sa.Text(), nullable=False),
        sa.Column('expected_behavior', sa.Text(), nullable=True),
        sa.Column('test_command', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('current_node', sa.String(length=128), nullable=True),
        sa.Column('thread_id', sa.String(length=128), nullable=True),
        sa.Column('approval_payload', sa.Text(), nullable=True),
        sa.Column('issue_context', sa.Text(), nullable=True),
        sa.Column('approval_status', sa.String(length=64), nullable=True),
        sa.Column('fix_strategy', sa.Text(), nullable=True),
        sa.Column('patch_diff', sa.Text(), nullable=True),
        sa.Column('test_result', sa.Text(), nullable=True),
        sa.Column('verification_result', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Text(), nullable=True),
        sa.Column('final_report', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)

    op.create_table(
        'run_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_run_events_id'), 'run_events', ['id'], unique=False)
    op.create_index(op.f('ix_run_events_run_id'), 'run_events', ['run_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_run_events_run_id'), table_name='run_events')
    op.drop_index(op.f('ix_run_events_id'), table_name='run_events')
    op.drop_table('run_events')
    op.drop_index(op.f('ix_agent_runs_id'), table_name='agent_runs')
    op.drop_table('agent_runs')
