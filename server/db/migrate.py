"""Bring the database schema up to date. Runs as an init container before the API starts.

    python -m server.db.migrate
"""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from server.db.database import engine

BASELINE_REVISION = "0001_baseline"

# Every API replica runs this on start. The lock makes the others wait, then find
# nothing to do, instead of racing to apply the same DDL.
MIGRATION_LOCK_ID = 7_400_001

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO)
    cfg = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))

    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
        try:
            inspector = inspect(conn)
            # Databases created before Alembic was adopted already hold the baseline
            # schema, so they are recorded as at the baseline rather than rebuilt.
            if not inspector.has_table(
                "alembic_version", schema="public"
            ) and inspector.has_table("users", schema="public"):
                logger.warning(
                    "Existing schema with no migration history; stamping %s",
                    BASELINE_REVISION,
                )
                command.stamp(cfg, BASELINE_REVISION)
            command.upgrade(cfg, "head")
        finally:
            conn.execute(
                text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID}
            )


if __name__ == "__main__":
    main()
