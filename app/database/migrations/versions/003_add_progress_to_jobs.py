"""Add progress tracking columns to jobs table

Revision ID: 003_add_progress_to_jobs
Revises: 002_rename_events_to_jobs
Create Date: 2026-02-02

This migration adds progress tracking columns:
- progress: Float percentage (0-100) with default 0
- progress_message: Optional human-readable progress message
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003_add_progress_to_jobs"
down_revision = "002_rename_events_to_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "jobs",
        sa.Column("progress_message", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "progress_message")
    op.drop_column("jobs", "progress")
