from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from server.db.database import get_db
from server.db.models import UserGroups, Groups
from server.db.models.users import Users
from typing import Optional
from datetime import datetime, timedelta
import jwt

from server.config import settings

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
    api_token: Optional[str] = Depends(api_key_header),
    jwt_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
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
                if user:
                    return user
        except HTTPException:
            # JWT token is invalid, continue to try API token
            pass

    # Fall back to API token (from api_token header)
    if api_token:
        user = db.query(Users).filter(Users.api_token == api_token).first()
        if user:
            return user

    # Neither token worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid JWT token or API token.",
    )


def verify_admin(
    user: Users = Depends(get_current_user), db: Session = Depends(get_db)
) -> Users:
    """
    Check if the user belongs to the admin group.
    """
    admin_group = db.query(Groups).filter(Groups.name == "admin").first()
    if not admin_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin group does not exist",
        )

    user_group = (
        db.query(UserGroups)
        .filter(UserGroups.userid == user.id, UserGroups.groupid == admin_group.id)
        .first()
    )

    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    return user


def log_user_action(
    user: Users,
    request_path: str,
    method: str,
    ip_address: str,
    json_data=None,
    db: Session = Depends(get_db),
):
    """
    Log user actions for auditing
    Will be implemented with full UserAction model
    """
    # This will be implemented when the UserAction model is fully ported
    pass
