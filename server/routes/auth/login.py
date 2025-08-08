"""Authentication endpoints for login/logout."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Union

from server.db.database import get_db
from server.db.models.users import Users
from server.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    LogoutResponse, 
    UserInfo,
    AuthErrorResponse
)
from server.auth.auth import create_access_token, get_current_user
from server.config import settings

router = APIRouter(tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    The username field can accept either username or email address.
    """
    # Try to find user by username first, then by email
    user = db.query(Users).filter(Users.username == login_data.username).first()
    
    if not user:
        # If not found by username, try by email
        user = db.query(Users).filter(Users.email == login_data.username).first()
    
    # Validate user exists and password is correct
    if not user or not user.check_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is verified
    if not user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified. Please check your email for verification instructions.",
        )
    
    # Create access token
    access_token_expires = timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "email": user.email},
        expires_delta=access_token_expires
    )
    
    # Create user info response
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        verified=user.verified,
        api_token=user.api_token
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=int(access_token_expires.total_seconds()),
        user=user_info
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: Users = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: With JWT tokens, logout is primarily handled client-side by 
    removing the token. This endpoint is provided for consistency and 
    potential future server-side session management.
    """
    # In a JWT-based system, logout is typically handled client-side
    # by removing the token from storage. We could implement a token 
    # blacklist here if needed in the future.
    
    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: Users = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        firstname=current_user.firstname,
        lastname=current_user.lastname,
        verified=current_user.verified,
        api_token=current_user.api_token
    )