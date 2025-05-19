from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.candidate import GWCandidate
from server.schemas.gw_alert import GWAlertSchema, GWCandidateSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["Events"])

@router.get("/candidate/event", response_model=List[GWCandidateSchema])
async def get_candidate_events(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get list of candidate events, optionally filtered by user."""
    query = db.query(GWCandidate)
    
    if user_id:
        query = query.filter(GWCandidate.user_id == user_id)
    
    candidates = query.all()
    return [GWCandidateSchema.from_orm(candidate) for candidate in candidates]


@router.post("/candidate/event")
async def create_candidate_event(
    candidate: GWCandidateSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new candidate event."""
    new_candidate = GWCandidate(
        name=candidate.name,
        ra=candidate.ra,
        dec=candidate.dec,
        error_radius=candidate.error_radius,
        user_id=current_user.id,
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
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Check if user is the owner or an admin
    if db_candidate.user_id != current_user.id and not current_user.adminuser:
        raise HTTPException(status_code=403, detail="Not authorized to update this candidate")
    
    # Update fields
    db_candidate.name = candidate.name
    db_candidate.ra = candidate.ra
    db_candidate.dec = candidate.dec
    db_candidate.error_radius = candidate.error_radius
    
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
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Check if user is the owner or an admin
    if db_candidate.user_id != current_user.id and not current_user.adminuser:
        raise HTTPException(status_code=403, detail="Not authorized to delete this candidate")
    
    db.delete(db_candidate)
    db.commit()
    
    return {"message": "Candidate deleted successfully"}
