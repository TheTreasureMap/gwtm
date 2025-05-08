from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from server.db.database import get_db
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
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
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
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(api_token: str = Depends(api_key_header), db: Session = Depends(get_db)) -> Optional[Users]:
    """
    Validate API token and return the associated user
    """
    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token is required",
        )
    
    user = db.query(Users).filter(Users.api_token == api_token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )
    
    # Log user action
    # Implementation of useractions logging will be added later
    
    return user

def verify_admin(user: Users = Depends(get_current_user)) -> Users:
    """
    Check if the user has admin privileges
    Currently checks for user ID 2 as per the original codebase
    """
    if user.id != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )
    return user

def get_admin_user(user: Users = Depends(get_current_user)) -> Users:
    """
    Check if the user has admin privileges and return user
    Uses adminuser flag instead of hard-coded ID
    """
    if not user.adminuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )
    return user

def log_user_action(user: Users, request_path: str, method: str, ip_address: str, json_data=None, db: Session = Depends(get_db)):
    """
    Log user actions for auditing
    Will be implemented with full UserAction model
    """
    # This will be implemented when the UserAction model is fully ported
    pass
