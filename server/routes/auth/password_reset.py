"""Forgot-password and reset-password endpoints."""

import logging
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import func
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.users import Users
from server.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
)
from server.utils.captcha import verify_captcha
from server.utils.email import send_password_reset_email
from server.utils.tokens import (
    RESET_TOKEN_EXPIRY_TEXT,
    decode_reset_token,
    generate_reset_token,
    reset_token_matches,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

INVALID_LINK = "This reset link is invalid or has already been used. Please request a new one."


async def _send_reset_email(email: str, username: str, token: str) -> None:
    try:
        await send_password_reset_email(email=email, username=username, reset_token=token)
    except Exception:
        logger.exception("Failed to send password reset email to %s", email)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Email a password reset link.

    Returns the same response whether or not the email is registered, and sends
    the email after the response so timing does not reveal it either.
    Requires `turnstile_token` when TURNSTILE_SECRET_KEY is configured.
    """
    await verify_captcha(request_data.turnstile_token)

    # Emails are stored as typed at registration, so match case-insensitively.
    user = (
        db.query(Users)
        .filter(func.lower(Users.email) == request_data.email.strip().lower())
        .first()
    )
    if user:
        token = generate_reset_token(user.id, user.password_hash)
        background_tasks.add_task(_send_reset_email, user.email, user.username, token)

    return MessageResponse(
        message=(
            "If an account with this email exists, a password reset link has been "
            f"sent. The link expires in {RESET_TOKEN_EXPIRY_TEXT}."
        )
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(reset_data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Set a new password from an emailed reset link.

    Completing a reset proves ownership of the email, so an unverified account
    is verified here too.

    The API token is kept by default because users' scripts depend on it; pass
    `rotate_api_token` to replace it when the account may be compromised. Login
    sessions are not revoked, but access tokens expire within
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    try:
        user_id, fingerprint = decode_reset_token(reset_data.token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired. Please request a new one.",
        )
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_LINK)

    # Row lock: a concurrent use of the same link waits here, then sees the new
    # hash and fails the fingerprint check, keeping the link single use.
    user = db.query(Users).filter(Users.id == user_id).with_for_update().first()
    if not user or not reset_token_matches(fingerprint, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_LINK)

    user.set_password(reset_data.password)
    if not user.verified:
        user.verified = True
        user.verification_key = None
    if reset_data.rotate_api_token or not user.api_token:
        user.api_token = secrets.token_hex(32)
    db.commit()

    logger.info(
        "Password reset for user %s (api token rotated: %s)",
        user.id,
        reset_data.rotate_api_token,
    )
    return MessageResponse(message="Your password has been reset. You can now log in.")
