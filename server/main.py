import os

from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import datetime
import uvicorn
import logging
import redis

from server.config import settings
from server.db.database import get_db, engine, Base
from server.db.models import Users, UserGroups, Groups, UserActions  # Import all models

from server.routes.pointing.router import router as pointing_router
from server.routes.instrument.router import router as instrument_router
from server.routes.admin.router import router as admin_router
from server.routes.candidate.router import router as candidate_router
from server.routes.doi.router import router as doi_router
from server.routes.gw_alert.router import router as gw_alert_router
from server.routes.gw_galaxy.router import router as galaxy_router
from server.routes.icecube.router import router as icecube_router
from server.routes.event.router import router as event
from server.routes.ui.router import router as ui_router
from server.routes.celestial.router import router as celestial_router
from server.routes.auth.router import router as auth_router
from server.routes.enums.router import router as enums_router

from contextlib import asynccontextmanager
from server.utils.error_handling import ErrorDetail

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_context(app: FastAPI):
    logger.info("Application is starting up...")
    # Create database tables with proper "IF NOT EXISTS" behaviour
    try:
        logger.info("Initialising database schema...")

        # Use checkfirst=True to avoid errors if tables already exist (production-safe)
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created/verified successfully!")

        # Create indexes if they don't exist (production-safe)
        with engine.connect() as conn:
            try:
                # Create performance index for pointing queries (matches Flask version)
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_pointing_status_id 
                    ON public.pointing(status, id);
                """
                )
                conn.commit()
                logger.info("Database indexes created/verified successfully!")
            except Exception as e:
                logger.warning(f"Index creation warning (may already exist): {e}")

    except Exception as e:
        logger.error(f"Failed to initialise database: {e}")
        # Don't raise - allow app to start even if DB setup fails (for debugging)

    yield

    logger.info("Application is shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Gravitational-Wave Treasure Map API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan_context,
)

# Define API version prefix
API_V1_PREFIX = "/api/v1"

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


async def lifespan_middleware(request: Request, call_next):
    try:
        # Initialize response here to avoid UnboundLocalError
        response = None
        # Your middleware logic
        response = await call_next(request)
        return response
    except Exception as e:
        # Error handling logic
        # Make sure response is defined even in exception paths
        if response is None:
            # Create a default error response
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )
        return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        errors.append(
            ErrorDetail(
                message=error["msg"],
                code="validation_error",
                params={
                    "field": (
                        ".".join(str(x) for x in error["loc"]) if error["loc"] else None
                    ),
                    "type": error["type"],
                },
            ).to_dict()
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Request validation error", "errors": errors},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy errors"""
    # Log the exception details for debugging
    logger.error(f"Database error: {str(exc)}")

    # Don't expose internal details to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "A database error occurred"},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Integrity error: {str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": "The request conflicts with database constraints"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTPException to ensure consistent format"""
    content = exc.detail

    # Ensure consistent format if detail is just a string
    if isinstance(content, str):
        content = {"message": content}

    return JSONResponse(
        status_code=exc.status_code, headers=exc.headers, content=content
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unhandled exceptions"""
    # Log the full exception details for debugging
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # Don't expose internal details to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred"},
    )


# API health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


@app.get("/service-status")
async def service_status(db: Session = Depends(get_db)):
    """
    Detailed service status endpoint that checks database and Redis connections.

    Returns:
        Dict with status of database and Redis connections, plus detailed info
    """
    status = {
        "database_status": "unknown",
        "redis_status": "unknown",
        "details": {"database": {}, "redis": {}},
    }

    # Check database connection with detailed info
    try:
        # Get connection parameters from settings
        db_host = settings.DB_HOST
        db_port = settings.DB_PORT
        db_name = settings.DB_NAME

        # Store connection info
        status["details"]["database"] = {
            "host": db_host,
            "port": db_port,
            "name": db_name,
        }

        # Test actual connection
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).first()
        if result and result[0] == 1:
            status["database_status"] = "connected"
        else:
            status["database_status"] = "disconnected"
    except Exception as e:
        status["database_status"] = "disconnected"
        status["details"]["database"]["error"] = str(e)

    # Check Redis connection with detailed info
    try:
        # Get Redis connection parameters
        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

        # Parse the URL for debug info
        if redis_url.startswith("redis://"):
            redis_host = redis_url.split("redis://")[1].split(":")[0]
            redis_port = redis_url.split(":")[-1].split("/")[0]
        else:
            redis_host = "unknown"
            redis_port = "unknown"

        # Store connection info
        status["details"]["redis"] = {
            "host": redis_host,
            "port": redis_port,
            "url": redis_url,
        }

        # Test actual connection
        try:
            redis_client = redis.from_url(redis_url)
            if redis_client.ping():
                status["redis_status"] = "connected"
            else:
                status["redis_status"] = "disconnected"
        except redis.exceptions.ConnectionError:
            status["redis_status"] = "disconnected"
            status["details"]["redis"]["error"] = "Connection refused"
    except Exception as e:
        status["redis_status"] = "disconnected"
        status["details"]["redis"]["error"] = str(e)

    return status


# Include routers with the API prefix
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(pointing_router, prefix=API_V1_PREFIX)
app.include_router(gw_alert_router, prefix=API_V1_PREFIX)
app.include_router(candidate_router, prefix=API_V1_PREFIX)
app.include_router(instrument_router, prefix=API_V1_PREFIX)
app.include_router(galaxy_router, prefix=API_V1_PREFIX)
app.include_router(icecube_router, prefix=API_V1_PREFIX)
app.include_router(doi_router, prefix=API_V1_PREFIX)
app.include_router(event, prefix=API_V1_PREFIX)
app.include_router(celestial_router, prefix=API_V1_PREFIX)
app.include_router(enums_router, prefix=API_V1_PREFIX)

# Include admin router without API prefix (matches original endpoint)
app.include_router(admin_router)

# Include UI-specific routes without the API prefix
app.include_router(ui_router)

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
