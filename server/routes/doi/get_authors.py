"""Get DOI authors endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from server.db.database import get_db
from server.db.models.doi_author import DOIAuthor, DOIAuthorGroup
from server.auth.auth import get_current_user
from server.schemas.doi import DOIAuthorSchema
from server.utils.error_handling import permission_exception

router = APIRouter(tags=["DOI"])


@router.get("/doi_authors/{group_id}", response_model=List[DOIAuthorSchema])
async def get_doi_authors(
        group_id: int,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get all DOI authors for a specific group.

    Parameters:
    - group_id: DOI author group ID

    Returns:
    - List of DOI authors
    """
    # First check if the group belongs to the user
    group = db.query(DOIAuthorGroup).filter(
        DOIAuthorGroup.id == group_id,
        DOIAuthorGroup.userid == user.id
    ).first()

    if not group:
        raise permission_exception("You don't have permission to access this DOI author group")

    authors = db.query(DOIAuthor).filter(DOIAuthor.author_groupid == group_id).all()
    return authors