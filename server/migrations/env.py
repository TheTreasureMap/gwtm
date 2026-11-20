from logging.config import fileConfig

from alembic import context
from geoalchemy2 import alembic_helpers
from sqlalchemy import create_engine, pool

from server.config import settings
from server.db.database import Base
import server.db.models  # noqa: F401  registers every table on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# The database default search_path is "postgis, public", which would make postgis the
# default schema and point autogenerate at PostGIS's own tables. Putting public first
# compares against the app's tables while still resolving the geography types.
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"options": "-csearch_path=public,postgis"},
    poolclass=pool.NullPool,
)

with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        include_object=alembic_helpers.include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()
