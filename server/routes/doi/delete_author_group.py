"""Delete DOI author group endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.doi_author import DOIAuthor, DOIAuthorGroup
from server.auth.auth import get_current_user

router = APIRouter(tags=["DOI"])


@router.delete("/doi_author_groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doi_author_group(
    group_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a DOI author group and all its authors."""
    group = (
        db.query(DOIAuthorGroup)
        .filter(DOIAuthorGroup.id == group_id, DOIAuthorGroup.userid == user.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author group not found")

    db.query(DOIAuthor).filter(DOIAuthor.author_groupid == group_id).delete()
    db.delete(group)
    db.commit()
