"""Resend verification email endpoint."""

import logging
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.users import Users, UserGroups, Groups
from server.auth.auth import get_current_user
from server.utils.email import send_verification_email

logger = logging.getLogger(__name__)

router = APIRouter(tags=["UI"])


@router.post("/ajax_resend_verification_email")
async def resend_verification_email(
    email: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Authenticated resend endpoint.

    With no `email` parameter, resends to the authenticated user (rarely
    useful in practice since unverified users cannot log in — kept for cases
    where a user's verification was reset after they were already
    authenticated, e.g. an admin-triggered re-verification).

    With an `email` parameter, resends to that user — restricted to members
    of the `admin` group. This is the path used by the admin user-list
    "Resend" action on the profile page.

    For the public, unauthenticated flow (user lost their original email),
    use POST /api/v1/auth/resend-verification instead.
    """
    if email:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        admin_group = db.query(Groups).filter(Groups.name == "admin").first()
        if not admin_group:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_group = (
            db.query(UserGroups)
            .filter(
                UserGroups.userid == current_user.id,
                UserGroups.groupid == admin_group.id,
            )
            .first()
        )
        if not user_group:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        user = current_user

    if user.verified:
        return {"message": "User is already verified"}

    token = secrets.token_urlsafe(32)
    user.verification_key = token
    db.commit()

    try:
        await send_verification_email(
            email=user.email,
            username=user.username,
            verification_token=token,
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", user.email)
        raise HTTPException(
            status_code=503,
            detail="Unable to send verification email. Please try again later.",
        )

    return {"message": "Verification email has been resent"}
