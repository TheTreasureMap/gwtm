"""Utility functions for event routes."""

from sqlalchemy import func
from sqlalchemy.orm import Session
from server.db.models.users import UserGroups, Groups


def is_admin(user, db: Session) -> bool:
    """Check if the user is an admin (case-insensitive group name match)."""
    admin_group = db.query(Groups).filter(func.lower(Groups.name) == "admin").first()
    if not admin_group:
        return False

    user_group = (
        db.query(UserGroups)
        .filter(UserGroups.userid == user.id, UserGroups.groupid == admin_group.id)
        .first()
    )

    return user_group is not None
