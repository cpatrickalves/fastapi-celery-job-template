"""Rename events table to jobs

Revision ID: 002_rename_events_to_jobs
Revises: 001_initial_event_schema
Create Date: 2026-01-23

This migration renames the events table to jobs and updates column names:
- Table: events -> jobs
- Column: event_type -> job_type
- Indexes are recreated with new naming convention
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "002_rename_events_to_jobs"
down_revision = "001_initial_event_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old indexes
    op.drop_index("ix_events_status_created", table_name="events")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")

    # Rename column event_type -> job_type
    op.alter_column("events", "event_type", new_column_name="job_type")

    # Rename table events -> jobs
    op.rename_table("events", "jobs")

    # Create new indexes with updated names
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_status_created", "jobs", ["status", "created_at"])


def downgrade() -> None:
    # Drop new indexes
    op.drop_index("ix_jobs_status_created", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")

    # Rename table jobs -> events
    op.rename_table("jobs", "events")

    # Rename column job_type -> event_type
    op.alter_column("events", "job_type", new_column_name="event_type")

    # Recreate old indexes
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_status_created", "events", ["status", "created_at"])
