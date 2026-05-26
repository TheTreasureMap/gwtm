"""User registration endpoints."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

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
from server.utils.tokens import generate_verification_token, decode_verification_token

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

        new_user = Users(
            username=register_data.username,
            email=register_data.email,
            firstname=register_data.first_name or "",
            lastname=register_data.last_name or "",
            verified=False,
            datecreated=datetime.utcnow(),
        )
        new_user.set_password(register_data.password)
        db.add(new_user)
        db.flush()  # assigns new_user.id so we can embed it in the JWT

        verification_token = generate_verification_token(new_user.id)
        new_user.verification_key = verification_token
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
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    verification_data: EmailVerificationRequest, db: Session = Depends(get_db)
):
    """Verify user email address using the signed verification token."""
    try:
        user_id = decode_verification_token(verification_data.verification_token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please request a new one.",
        )
    except (InvalidTokenError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user = (
        db.query(Users)
        .filter(
            Users.id == user_id,
            Users.verification_key == verification_data.verification_token,
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.verified:
        return EmailVerificationResponse(
            message="Email address is already verified", verified=True
        )

    user.verified = True
    user.verification_key = None
    db.commit()

    return EmailVerificationResponse(
        message="Email verified successfully! You can now log in.", verified=True
    )


@router.post("/resend-verification", response_model=RegisterResponse)
async def resend_verification_email(email: str, db: Session = Depends(get_db)):
    """
    Public, unauthenticated resend endpoint.

    Returns the same generic response regardless of whether the email exists
    or whether the account is already verified, to avoid leaking account state.
    """
    generic_response = RegisterResponse(
        message="If an account with this email exists and is unverified, a verification email has been sent.",
        email=email,
        verification_required=True,
    )

    try:
        user = db.query(Users).filter(Users.email == email).first()

        if not user or user.verified:
            return generic_response

        verification_token = generate_verification_token(user.id)
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

        return generic_response

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email. Please try again.",
        )
