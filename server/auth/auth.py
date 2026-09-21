import logging
import re

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from server.db.database import get_db
from server.db.models import UserGroups, Groups
from server.db.models.users import Users
from typing import Optional
from datetime import datetime, timedelta
import jwt

from server.config import settings
from server.utils.audit import record_user_action, request_body_json

logger = logging.getLogger("gwtm.auth")

# Define the API key header
api_key_header = APIKeyHeader(name="api_token", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Largest body inspected for a deprecated api_token-in-body credential.
MAX_BODY_TOKEN_BYTES = 4 * 1024 * 1024
# What an HTTP header could carry; anything else (NUL, lone surrogates) breaks the DB driver.
_TOKEN_CHARS = re.compile(r"[ -~]+")
BODY_TOKEN_DEPRECATION_WARNING = (
    "Passing api_token in the request body is deprecated and will be "
    "removed. Send it in the api_token header instead."
)


async def buffer_body_for_token_fallback(request: Request) -> None:
    """Read a bounded body onto the request; sync dependencies can't await it."""
    length = request.headers.get("content-length", "")
    if length.isdigit() and int(length) <= MAX_BODY_TOKEN_BYTES:
        await request.body()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time

    Returns:
        JWT token as a string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode a JWT token

    Args:
        token: JWT token

    Returns:
        Decoded payload
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_current_user(
    request: Request,
    api_token: Optional[str] = Depends(api_key_header),
    jwt_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    _buffered: None = Depends(buffer_body_for_token_fallback),
) -> Optional[Users]:
    """
    Validate JWT token or API token and return the associated user.
    JWT tokens take precedence over API tokens.
    """
    user = None

    # Try JWT token first (from Authorization header)
    if jwt_token:
        try:
            payload = decode_token(jwt_token)
            user_id = payload.get("sub")
            if user_id:
                user = db.query(Users).filter(Users.id == int(user_id)).first()
        except HTTPException:
            # JWT token is invalid, continue to try API token
            user = None

    # Fall back to API token (from api_token header)
    if not user and api_token:
        user = db.query(Users).filter(Users.api_token == api_token).first()

    # Also accept API token passed as a Bearer token (jwt_token that failed JWT decode)
    if not user and jwt_token:
        user = db.query(Users).filter(Users.api_token == jwt_token).first()

    # Deprecated: api_token in the JSON body, for old-API scripts.
    if not user:
        body = request_body_json(request, max_bytes=MAX_BODY_TOKEN_BYTES)
        body_token = body.get("api_token") if isinstance(body, dict) else None
        if isinstance(body_token, str) and _TOKEN_CHARS.fullmatch(body_token):
            user = db.query(Users).filter(Users.api_token == body_token).first()
            if user:
                logger.warning(
                    "Deprecated api_token-in-body auth used by userid=%s username=%r at %s",
                    user.id,
                    user.username,
                    request.url.path,
                )
                request.state.deprecated_body_token = True

    # Neither token worked
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token or API token.",
        )

    record_user_action(user, request)
    return user


def is_admin_user(user: Users, db: Session) -> bool:
    """Return True if the user belongs to the admin group."""
    return (
        db.query(UserGroups)
        .join(Groups, UserGroups.groupid == Groups.id)
        .filter(
            UserGroups.userid == user.id,
            func.lower(Groups.name) == "admin",
        )
        .first()
    ) is not None


def verify_admin(
    user: Users = Depends(get_current_user), db: Session = Depends(get_db)
) -> Users:
    """
    Check if the user belongs to the admin group (case-insensitive).
    """
    if not is_admin_user(user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )
    return user
