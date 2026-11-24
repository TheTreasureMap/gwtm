"""Index pointing on (status, id).

Dev already has this index and prod does not, hence if_not_exists. The pointing
table is small (about 50k rows), so a plain build holds its write lock for well
under a second and CONCURRENTLY is not needed.

Revision ID: 0002_pointing_status_index
Revises: 0001_baseline
Create Date: 2026-11-24
"""

from alembic import op

revision = "0002_pointing_status_index"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "idx_pointing_status_id",
        "pointing",
        ["status", "id"],
        schema="public",
        if_not_exists=True,
    )


def downgrade():
    op.drop_index(
        "idx_pointing_status_id",
        table_name="pointing",
        schema="public",
        if_exists=True,
    )
