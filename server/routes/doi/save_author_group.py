"""Create and update DOI author group endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.doi_author import DOIAuthor, DOIAuthorGroup
from server.auth.auth import get_current_user
from server.schemas.doi import DOIAuthorGroupSave, DOIAuthorGroupSchema

router = APIRouter(tags=["DOI"])


@router.post("/doi_author_groups", response_model=DOIAuthorGroupSchema, status_code=status.HTTP_201_CREATED)
async def create_doi_author_group(
    body: DOIAuthorGroupSave,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new DOI author group with its authors."""
    group = DOIAuthorGroup(name=body.name, userid=user.id)
    db.add(group)
    db.flush()

    for author in body.authors:
        db.add(DOIAuthor(
            name=author.name,
            affiliation=author.affiliation,
            orcid=author.orcid,
            gnd=author.gnd,
            author_groupid=group.id,
        ))

    db.commit()
    db.refresh(group)
    return group


@router.put("/doi_author_groups/{group_id}", response_model=DOIAuthorGroupSchema)
async def update_doi_author_group(
    group_id: int,
    body: DOIAuthorGroupSave,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a DOI author group name and sync its authors."""
    group = (
        db.query(DOIAuthorGroup)
        .filter(DOIAuthorGroup.id == group_id, DOIAuthorGroup.userid == user.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author group not found")

    group.name = body.name

    submitted_ids = {a.id for a in body.authors if a.id is not None}

    # Delete authors removed from the list
    for existing in db.query(DOIAuthor).filter(DOIAuthor.author_groupid == group_id).all():
        if existing.id not in submitted_ids:
            db.delete(existing)

    # Update existing / insert new
    for author in body.authors:
        if author.id is not None:
            existing = db.query(DOIAuthor).filter(DOIAuthor.id == author.id).first()
            if existing:
                existing.name = author.name
                existing.affiliation = author.affiliation
                existing.orcid = author.orcid
                existing.gnd = author.gnd
        else:
            db.add(DOIAuthor(
                name=author.name,
                affiliation=author.affiliation,
                orcid=author.orcid,
                gnd=author.gnd,
                author_groupid=group_id,
            ))

    db.commit()
    db.refresh(group)
    return group
