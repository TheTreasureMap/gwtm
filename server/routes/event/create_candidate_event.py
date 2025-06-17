"""Create candidate event endpoint."""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import GWCandidateCreate
from server.core.enums.depthunit import DepthUnit as depth_unit_enum
from server.auth.auth import get_current_user

router = APIRouter(tags=["Events"])


@router.post("/candidate/event")
async def create_candidate_event(
    candidate: GWCandidateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new candidate event."""
    # Create a POINT WKT string for position
    position = f"POINT({candidate.ra} {candidate.dec})"
    
    new_candidate = GWCandidate(
        candidate_name=candidate.candidate_name,
        graceid=candidate.graceid, # Required field for GWCandidate
        position=position,  # Set position from ra and dec
        submitterid=current_user.id,
        magnitude_unit=depth_unit_enum.ab_mag, # Default required field
        datecreated=datetime.now()
    )
    
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    return {"message": "Candidate created successfully", "id": new_candidate.id}
