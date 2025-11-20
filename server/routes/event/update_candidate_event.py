"""Update candidate event endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import GWCandidateSchema
from server.utils.error_handling import not_found_exception, permission_exception
from server.auth.auth import get_current_user
from .utils import is_admin

router = APIRouter(tags=["Events"])


@router.put("/candidate/event/{candidate_id}")
async def update_candidate_event(
    candidate_id: int,
    candidate: GWCandidateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing candidate event."""
    db_candidate = db.query(GWCandidate).filter(GWCandidate.id == candidate_id).first()

    if not db_candidate:
        raise not_found_exception("Candidate not found")

    # Check if user is the owner or an admin
    if db_candidate.submitterid != current_user.id and not is_admin(current_user, db):
        raise permission_exception("Not authorized to update this candidate")

    # Update fields
    db_candidate.candidate_name = candidate.candidate_name

    # Update position from ra and dec if provided
    if candidate.ra is not None and candidate.dec is not None:
        position = f"POINT({candidate.ra} {candidate.dec})"
        db_candidate.position = position

    db.commit()
    db.refresh(db_candidate)

    return {"message": "Candidate updated successfully"}
