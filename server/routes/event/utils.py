"""Utility functions for event routes."""

from sqlalchemy.orm import Session
from server.auth.auth import is_admin_user


def is_admin(user, db: Session) -> bool:
    """Check if the user is an admin."""
    return is_admin_user(user, db)
