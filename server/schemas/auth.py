"""Authentication schemas for login/logout endpoints."""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Request schema for user login."""
    
    username: str
    password: str
    remember_me: bool = False
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username is required')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Password is required')
        return v


class LoginResponse(BaseModel):
    """Response schema for successful login."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: "UserInfo"


class UserInfo(BaseModel):
    """User information included in login response."""
    
    id: int
    username: str
    email: str
    firstname: str
    lastname: str
    verified: bool
    api_token: Optional[str] = None


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    
    message: str = "Successfully logged out"


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh."""
    
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Response schema for token refresh."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthErrorResponse(BaseModel):
    """Error response schema for authentication failures."""
    
    detail: str
    error_code: Optional[str] = None


# Update forward references
LoginResponse.model_rebuild()