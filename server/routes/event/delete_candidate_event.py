"""Delete candidate event endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.utils.error_handling import not_found_exception, permission_exception
from server.auth.auth import get_current_user
from server.utils.audit import log_admin_action
from .utils import is_admin

router = APIRouter(tags=["Events"])


@router.delete("/candidate/event/{candidate_id}")
async def delete_candidate_event(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a candidate event."""
    db_candidate = db.query(GWCandidate).filter(GWCandidate.id == candidate_id).first()

    if not db_candidate:
        raise not_found_exception("Candidate not found")

    # Check if user is the owner or an admin
    is_owner = db_candidate.submitterid == current_user.id
    if not is_owner and not is_admin(current_user, db):
        raise permission_exception("Not authorized to delete this candidate")

    # Read off the details while the instance is still live; it is expired
    # once the delete is committed.
    candidate_name = db_candidate.candidate_name
    graceid = db_candidate.graceid

    db.delete(db_candidate)
    db.commit()

    log_admin_action(
        current_user,
        "candidate_event.delete",
        f"candidate:{candidate_id}",
        admin_override=not is_owner,
        candidate_name=candidate_name,
        graceid=graceid,
    )

    return {"message": "Candidate deleted successfully"}
