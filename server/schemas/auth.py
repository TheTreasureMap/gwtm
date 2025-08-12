"""Authentication schemas for login/logout endpoints."""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Request schema for user login."""

    username: str
    password: str
    remember_me: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError("Username is required")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 1:
            raise ValueError("Password is required")
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
    # TODO: Re-enable when database is migrated
    # verified: bool
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


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError("Username is required")
        
        # Check length
        username = v.strip()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username) > 50:
            raise ValueError("Username must be no more than 50 characters long")
        
        # Check allowed characters
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username can only contain letters, numbers, underscores, and dashes")
        
        return username

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password is required")
        
        # Password strength requirements
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        
        return v

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v):
        if v and len(v.strip()) > 100:
            raise ValueError("Name must be no more than 100 characters long")
        return v.strip() if v else None


class RegisterResponse(BaseModel):
    """Response schema for user registration."""

    message: str
    email: str
    verification_required: bool = True


class EmailVerificationRequest(BaseModel):
    """Request schema for email verification."""
    
    verification_token: str


class EmailVerificationResponse(BaseModel):
    """Response schema for email verification."""
    
    message: str
    verified: bool


class AuthErrorResponse(BaseModel):
    """Error response schema for authentication failures."""

    detail: str
    error_code: Optional[str] = None


# Update forward references
LoginResponse.model_rebuild()
