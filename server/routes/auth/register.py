"""User registration endpoints."""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from server.db.database import get_db
from server.db.models.users import Users
from server.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    AuthErrorResponse,
)
from server.utils.email import send_verification_email
from server.config import settings

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=RegisterResponse)
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user account with email verification required.
    The user will receive a verification email to activate their account.
    """
    try:
        # Check if username already exists
        existing_user = db.query(Users).filter(
            (Users.username == register_data.username) | 
            (Users.email == register_data.email)
        ).first()
        
        if existing_user:
            if existing_user.email == register_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email address already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken"
                )
        
        # TODO: Re-enable verification when database is migrated
        # verification_token = secrets.token_urlsafe(32)
        # verification_expires = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        
        # Create new user (without verification for Flask compatibility)
        new_user = Users(
            username=register_data.username,
            email=register_data.email,
            firstname=register_data.first_name or "",
            lastname=register_data.last_name or "",
            # verified=False,  # Account starts unverified
            datecreated=datetime.utcnow(),
            # verification_key=verification_token,
            # verification_expires=verification_expires
        )
        
        # Set password (this will hash it automatically via the model)
        new_user.set_password(register_data.password)
        
        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # TODO: Re-enable email verification when database is migrated
        # try:
        #     await send_verification_email(
        #         email=new_user.email,
        #         username=new_user.username,
        #         verification_token=verification_token
        #     )
        # except Exception as e:
        #     # Log the error but don't fail registration
        #     print(f"Failed to send verification email: {e}")
        #     # In production, you might want to queue this for retry
        
        return RegisterResponse(
            message="Registration successful! You can now log in with your credentials.",
            email=new_user.email,
            verification_required=False
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest, 
    db: Session = Depends(get_db)
):
    """
    Verify user email address using verification token.
    """
    try:
        # Find user by verification token
        user = db.query(Users).filter(
            Users.verification_key == verification_data.verification_token
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if token has expired
        if user.verification_expires and user.verification_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired. Please register again."
            )
        
        # Check if already verified
        if user.verified:
            return EmailVerificationResponse(
                message="Email address is already verified",
                verified=True
            )
        
        # Verify the account
        user.verified = True
        user.verification_key = None  # Clear the token
        user.verification_expires = None
        
        db.commit()
        
        return EmailVerificationResponse(
            message="Email verified successfully! You can now log in.",
            verified=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again."
        )


@router.post("/resend-verification", response_model=RegisterResponse)
async def resend_verification_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Resend verification email to user.
    """
    try:
        # Find user by email
        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
            # Don't reveal if email exists for security
            return RegisterResponse(
                message="If an account with this email exists, a verification email has been sent.",
                email=email,
                verification_required=True
            )
        
        # Check if already verified
        if user.verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is already verified"
            )
        
        # Generate new verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Update user with new token
        user.verification_key = verification_token
        user.verification_expires = verification_expires
        
        db.commit()
        
        # Send verification email
        try:
            await send_verification_email(
                email=user.email,
                username=user.username,
                verification_token=verification_token
            )
        except Exception as e:
            print(f"Failed to send verification email: {e}")
        
        return RegisterResponse(
            message="If an account with this email exists, a verification email has been sent.",
            email=email,
            verification_required=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email. Please try again."
        )