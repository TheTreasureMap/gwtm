"""Get DOI author groups endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from server.db.database import get_db
from server.db.models.doi_author import DOIAuthorGroup
from server.auth.auth import get_current_user
from server.schemas.doi import DOIAuthorGroupSchema

router = APIRouter(tags=["DOI"])


@router.get("/doi_author_groups", response_model=List[DOIAuthorGroupSchema])
async def get_doi_author_groups(
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get all DOI author groups for the current user.

    Returns:
    - List of DOI author groups
    """
    groups = db.query(DOIAuthorGroup).filter(DOIAuthorGroup.userid == user.id).all()
    return groups