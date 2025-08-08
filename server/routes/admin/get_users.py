"""Get all users endpoint for admin."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from server.db.database import get_db
from server.db.models.users import Users
from server.auth.auth import verify_admin
from server.schemas.users import UserResponse

router = APIRouter(tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    db: Session = Depends(get_db), 
    admin_user: Users = Depends(verify_admin)
):
    """
    Get all users in the system. Admin only.
    
    Returns:
    - List of all users with basic information
    """
    users = db.query(Users).order_by(Users.datecreated.asc()).all()
    return users