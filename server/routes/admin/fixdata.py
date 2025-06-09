"""Fix data endpoint for admin users."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.auth.auth import verify_admin

router = APIRouter(tags=["admin"])


@router.get("/fixdata")
@router.post("/fixdata")
async def fixdata(
        db: Session = Depends(get_db),
        user=Depends(verify_admin)  # Only admin can use this endpoint
):
    """
    Fix data issues (admin only).

    This endpoint is for administrative purposes.
    For backward compatibility, it just verifies admin access and returns success.
    """
    return {"message": "success"}