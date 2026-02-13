"""Add cancelled_at column to jobs table

Revision ID: 004_add_cancelled_at_to_jobs
Revises: 003_add_progress_to_jobs
Create Date: 2026-02-12

This migration adds a cancelled_at timestamp column to support
job cancellation tracking.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "004_add_cancelled_at_to_jobs"
down_revision = "003_add_progress_to_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "cancelled_at")
