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
    
    # PostGIS setup - work with existing PostGIS extension
    with engine.connect() as conn:
        # PostGIS is already installed, just ensure we can use geography types
        # Set search path to include both public and postgis schemas
        conn.execute(text("SET search_path TO public, postgis;"))
        conn.commit()
    
    # Use an engine with PostGIS search path for table creation
    from sqlalchemy.pool import StaticPool
    engine_with_postgis = create_engine(
        database_url, 
        connect_args={'options': '-csearch_path=public,postgis'},
        poolclass=StaticPool
    )
    
    # Create all tables using FastAPI models (equivalent to Flask's db.create_all())
    Base.metadata.create_all(bind=engine_with_postgis)
    
    # Create additional indexes (exactly matching Flask setup)
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX idx_pointing_status_id ON public.pointing(status, id);"))
        conn.commit()
    
    print("FastAPI database schema created successfully")
    print(f"Created tables: {list(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    create_database_tables()