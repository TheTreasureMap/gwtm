import logging

from fastapi import Depends, HTTPException, Request, Response, status
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
    # FastAPI only special-cases this as the real Response for injection (and
    # sets a fresh one per request) when the annotation is bare Response, not
    # Optional[Response]/Response | None, wrapping it breaks route building
    # entirely. The mismatched `= None` default only matters for tests that
    # call this function directly, bypassing FastAPI's injection.
    response: Response = None,
    api_token: Optional[str] = Depends(api_key_header),
    jwt_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[Users]:
    """
    Validate JWT token or API token and return the associated user.
    JWT tokens take precedence over API tokens.
    """
    user = None
    deprecated_body_token = False

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

    # Deprecated: api_token in the JSON body, for scripts written against the
    # old API. request_body_json only sees a body FastAPI has already parsed
    # for the endpoint's own use (reading the stream again here would consume
    # it before the endpoint gets to), so this only works on endpoints that
    # declare a body of their own. A body-less endpoint (e.g. /admin/fixdata)
    # can't authenticate this way, harmless in practice, everything an
    # external script would actually POST data to already has a body schema.
    # max_bytes=None: the audit-retention cap doesn't belong here, a large
    # but otherwise valid body shouldn't fail auth just because it's too big
    # to bother persisting in the audit log.
    if not user:
        body = request_body_json(request, max_bytes=None)
        body_token = body.get("api_token") if isinstance(body, dict) else None
        if isinstance(body_token, str) and body_token:
            user = db.query(Users).filter(Users.api_token == body_token).first()
            deprecated_body_token = user is not None

    # Neither token worked
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token or API token.",
        )

    if deprecated_body_token:
        logger.warning(
            "Deprecated api_token-in-body auth used by userid=%s username=%r at %s",
            user.id,
            user.username,
            request.url.path,
        )
        if response is not None:
            response.headers["X-Deprecation-Warning"] = (
                "Passing api_token in the request body is deprecated and will be "
                "removed. Send it in the api_token header instead."
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
