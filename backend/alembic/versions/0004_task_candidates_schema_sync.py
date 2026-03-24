"""sync task_candidates schema with model

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_candidates", sa.Column("assignees_display", sa.String(length=500), nullable=True))
    op.add_column("task_candidates", sa.Column("coordinator", sa.String(length=255), nullable=True))
    op.add_column(
        "task_candidates",
        sa.Column("item_kind", sa.String(length=50), nullable=False, server_default="task"),
    )
    op.add_column(
        "task_candidates",
        sa.Column("discussed_flag", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "task_candidates",
        sa.Column("skipped_discussion_flag", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("task_candidates", "skipped_discussion_flag")
    op.drop_column("task_candidates", "discussed_flag")
    op.drop_column("task_candidates", "item_kind")
    op.drop_column("task_candidates", "coordinator")
    op.drop_column("task_candidates", "assignees_display")
