from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.gw_alert import GWCandidateSchema, GWCandidateCreate
from server.core.enums.depth_unit import depth_unit as depth_unit_enum
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception
from server.auth.auth import get_current_user
from server.db.models.users import UserGroups, Groups

def is_admin(user, db: Session) -> bool:
    """Check if the user is an admin."""
    admin_group = db.query(Groups).filter(Groups.name == "admin").first()
    if not admin_group:
        return False
    
    user_group = db.query(UserGroups).filter(
        UserGroups.userid == user.id, 
        UserGroups.groupid == admin_group.id
    ).first()
    
    return user_group is not None

router = APIRouter(tags=["Events"])

@router.get("/candidate/event", response_model=List[GWCandidateSchema])
async def get_candidate_events(
    id: Optional[int] = Query(None, description="Filter by candidate ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of candidate events, optionally filtered by user or ID."""
    query = db.query(GWCandidate)
    
    if id:
        query = query.filter(GWCandidate.id == id)
    
    if user_id:
        query = query.filter(GWCandidate.submitterid == user_id)
    
    candidates = query.all()
    return candidates

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

@router.put("/candidate/event/{candidate_id}")
async def update_candidate_event(
    candidate_id: int,
    candidate: GWCandidateSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
