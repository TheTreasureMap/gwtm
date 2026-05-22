"""User registration endpoints."""

import logging
import secrets
from datetime import datetime
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

logger = logging.getLogger(__name__)

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
        existing_user = (
            db.query(Users)
            .filter(
                (Users.username == register_data.username)
                | (Users.email == register_data.email)
            )
            .first()
        )

        if existing_user:
            if existing_user.email == register_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email address already exists",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken",
                )

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Create new user with account unverified until email is confirmed
        new_user = Users(
            username=register_data.username,
            email=register_data.email,
            firstname=register_data.first_name or "",
            lastname=register_data.last_name or "",
            verified=False,
            datecreated=datetime.utcnow(),
            verification_key=verification_token,
        )

        # Set password (this will hash it automatically via the model)
        new_user.set_password(register_data.password)

        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        email_sent = True
        try:
            await send_verification_email(
                email=new_user.email,
                username=new_user.username,
                verification_token=verification_token,
            )
        except Exception:
            # Account creation succeeded; surface a degraded message so the user
            # knows to retry rather than waiting for an email that never sent.
            email_sent = False
            logger.exception("Failed to send verification email to %s", new_user.email)

        message = (
            "Registration successful! Please check your email to verify your account before logging in."
            if email_sent
            else "Registration successful, but we couldn't send your verification email. Please use the resend option on your profile or contact support."
        )

        return RegisterResponse(
            message=message,
            email=new_user.email,
            verification_required=True,
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest, db: Session = Depends(get_db)
):
    """
    Verify user email address using verification token.
    """
    try:
        # Find user by verification token
        user = (
            db.query(Users)
            .filter(Users.verification_key == verification_data.verification_token)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        # Check if already verified
        if user.verified:
            return EmailVerificationResponse(
                message="Email address is already verified", verified=True
            )

        # Verify the account
        user.verified = True
        user.verification_key = None

        db.commit()

        return EmailVerificationResponse(
            message="Email verified successfully! You can now log in.", verified=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again.",
        )


@router.post("/resend-verification", response_model=RegisterResponse)
async def resend_verification_email(email: str, db: Session = Depends(get_db)):
    """
    Public, unauthenticated resend endpoint.

    Intended for users who registered but never received (or lost) their
    verification email and therefore cannot log in. Returns the same generic
    response regardless of whether the email exists or whether the account is
    already verified, to avoid leaking account state to unauthenticated
    callers. For admin-driven resends on behalf of another user, use the
    authenticated /ajax_resend_verification_email endpoint instead.
    """
    generic_response = RegisterResponse(
        message="If an account with this email exists and is unverified, a verification email has been sent.",
        email=email,
        verification_required=True,
    )

    try:
        user = db.query(Users).filter(Users.email == email).first()

        # Don't reveal whether the email exists, or whether the account is
        # already verified — both leak account state to anonymous callers.
        if not user or user.verified:
            return generic_response

        verification_token = secrets.token_urlsafe(32)
        user.verification_key = verification_token
        db.commit()

        try:
            await send_verification_email(
                email=user.email,
                username=user.username,
                verification_token=verification_token,
            )
        except Exception:
            logger.exception("Failed to send verification email to %s", user.email)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to send verification email. Please try again later.",
            )

        return generic_response

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email. Please try again.",
        )
