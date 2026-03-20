"""init

Revision ID: 0001
Revises:
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "protocols",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("original_file_path", sa.String(length=500), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("draft_saved_at", sa.DateTime(), nullable=True),
        sa.Column("normalized_docx_path", sa.String(length=500), nullable=True),
        sa.Column("published_docx_path", sa.String(length=500), nullable=True),
        sa.Column("bitrix_smart_process_id", sa.String(length=100), nullable=True),
        sa.Column("bitrix_publish_status", sa.String(length=50), nullable=True),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("protocol_id", sa.Integer(), sa.ForeignKey("protocols.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=20), nullable=False, server_default="auto"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_table(
        "task_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("protocol_id", sa.Integer(), sa.ForeignKey("protocols.id"), nullable=False),
        sa.Column("topic_id", sa.Integer(), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("source_fragment", sa.Text(), nullable=False, server_default=""),
        sa.Column("normalized_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("topic_auto_candidate", sa.String(length=255), nullable=True),
        sa.Column("topic_candidate_list", sa.JSON(), nullable=False),
        sa.Column("assignee_raw", sa.String(length=255), nullable=True),
        sa.Column("assignee_b24_id", sa.String(length=100), nullable=True),
        sa.Column("assignee_b24_name", sa.String(length=255), nullable=True),
        sa.Column("deadline_raw", sa.String(length=100), nullable=True),
        sa.Column("deadline_iso", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bitrix_task_id", sa.String(length=100), nullable=True),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("protocol_id", sa.Integer(), sa.ForeignKey("protocols.id"), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("task_candidates")
    op.drop_table("topics")
    op.drop_table("protocols")
