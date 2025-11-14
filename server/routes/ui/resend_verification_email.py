"""Resend verification email endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.users import Users
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])


@router.post("/ajax_resend_verification_email")
async def resend_verification_email(
    email: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Resend the verification email to a user."""
    from server.utils.email import send_account_validation_email

    # If email is provided, find that user (admin function)
    # Otherwise use the current user
    if email:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Only allow admins to send verification emails to other users
        # Note: Need to check if user is admin
        from server.db.models.users import UserGroups, Groups

        admin_group = db.query(Groups).filter(Groups.name == "admin").first()
        if admin_group:
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

    # Send the verification email
    send_account_validation_email(user, db)

    return {"message": "Verification email has been resent"}
