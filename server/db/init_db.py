"""FastAPI database initialization script."""

import os
from sqlalchemy import create_engine, text
from server.db.database import Base, engine as default_engine
from server.db.models import *  # Import all models to register them


def create_database_tables():
    """Create database tables using FastAPI models - exactly matching Flask setup."""
    # Use environment variables to override the default database connection
    db_user = os.environ.get("DB_USER")
    db_pwd = os.environ.get("DB_PWD") 
    db_name = os.environ.get("DB_NAME")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    
    # If environment variables are provided, create a custom engine
    if all([db_user, db_pwd, db_name, db_host, db_port]):
        database_url = f"postgresql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(database_url)
    else:
        # Use the default engine from FastAPI database configuration
        engine = default_engine
    
    # PostGIS setup - create extension in public schema for FastAPI table creation
    with engine.connect() as conn:
        # Drop existing PostGIS extension if it exists (from init scripts)
        conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
                    DROP EXTENSION postgis CASCADE;
                END IF;
            END
            $$;
        """))
        # Create PostGIS extension in public schema so geography types are accessible
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("SET search_path TO public;"))
        conn.commit()
    
    # Create all tables using FastAPI models (equivalent to Flask's db.create_all())
    Base.metadata.create_all(bind=engine)
    
    # Create additional indexes (matching Flask setup)
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pointing_status_id ON public.pointing(status, id);"))
        conn.commit()
    
    print("FastAPI database schema created successfully")
    print(f"Created tables: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    create_database_tables()