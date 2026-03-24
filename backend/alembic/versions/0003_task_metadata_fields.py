"""add task metadata fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-23
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_candidates", sa.Column("section_name", sa.String(length=100), nullable=True))
    op.add_column("task_candidates", sa.Column("parent_context", sa.String(length=255), nullable=True))
    op.add_column("task_candidates", sa.Column("context_label", sa.String(length=100), nullable=True))
    op.add_column("task_candidates", sa.Column("assignees_raw", sa.Text(), nullable=True))
    op.add_column("task_candidates", sa.Column("assignees_normalized", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("task_candidates", sa.Column("deadline_kind", sa.String(length=50), nullable=True))
    op.add_column("task_candidates", sa.Column("deadline_note", sa.String(length=255), nullable=True))
    op.add_column("task_candidates", sa.Column("markers", sa.JSON(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("task_candidates", "markers")
    op.drop_column("task_candidates", "deadline_note")
    op.drop_column("task_candidates", "deadline_kind")
    op.drop_column("task_candidates", "assignees_normalized")
    op.drop_column("task_candidates", "assignees_raw")
    op.drop_column("task_candidates", "context_label")
    op.drop_column("task_candidates", "parent_context")
    op.drop_column("task_candidates", "section_name")
