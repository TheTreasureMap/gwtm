"""Get candidate events endpoint."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import GWCandidateSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["Events"])


@router.get("/candidate/event", response_model=List[GWCandidateSchema])
async def get_candidate_events(
    id: Optional[int] = Query(None, description="Filter by candidate ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of candidate events, optionally filtered by user or ID."""
    query = db.query(GWCandidate)

    if id:
        query = query.filter(GWCandidate.id == id)

    if user_id:
        query = query.filter(GWCandidate.submitterid == user_id)

    candidates = query.all()
    return candidates
