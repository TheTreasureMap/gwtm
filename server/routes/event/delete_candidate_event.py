"""Delete candidate event endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.utils.error_handling import not_found_exception, permission_exception
from server.auth.auth import get_current_user
from .utils import is_admin

router = APIRouter(tags=["Events"])


@router.delete("/candidate/event/{candidate_id}")
async def delete_candidate_event(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a candidate event."""
    db_candidate = db.query(GWCandidate).filter(GWCandidate.id == candidate_id).first()
    
    if not db_candidate:
        raise not_found_exception("Candidate not found")
    
    # Check if user is the owner or an admin
    if db_candidate.submitterid != current_user.id and not is_admin(current_user, db):
        raise permission_exception("Not authorized to delete this candidate")
    
    db.delete(db_candidate)
    db.commit()
    
    return {"message": "Candidate deleted successfully"}