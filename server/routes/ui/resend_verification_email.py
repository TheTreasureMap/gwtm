"""Resend verification email endpoint."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.users import Users, UserGroups, Groups
from server.auth.auth import get_current_user
from server.utils.email import send_verification_email
from server.utils.tokens import generate_verification_token

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

    With no `email` parameter, resends to the authenticated user.
    With an `email` parameter, resends to that user — restricted to admins.
    Admin check happens before any email lookup to prevent enumeration.
    """
    if email:
        # Authorise first — before touching the DB for the target user — so
        # non-admins always get 403 regardless of whether the email exists.
        admin_group = db.query(Groups).filter(Groups.name == "admin").first()
        is_admin = admin_group and db.query(UserGroups).filter(
            UserGroups.userid == current_user.id,
            UserGroups.groupid == admin_group.id,
        ).first()
        if not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    else:
        user = current_user

    if user.verified:
        return {"message": "User is already verified"}

    token = generate_verification_token(user.id)
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
