"""Delete candidates endpoint."""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import DeleteCandidateParams, DeleteCandidateResponse
from server.auth.auth import get_current_user
from server.utils.error_handling import (
    not_found_exception,
    permission_exception,
    validation_exception,
)

router = APIRouter(tags=["candidates"])


@router.delete("/candidate", response_model=DeleteCandidateResponse)
async def delete_candidates(
    delete_params: DeleteCandidateParams = Body(..., description="Fields to delete"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Delete candidate(s).

    Provide either:
    - A single candidate ID to delete
    - A list of candidate IDs to delete

    Only the owner of a candidate can delete it.
    Returns information about deleted candidates and any warnings.
    """
    warnings = []
    candidates_to_delete = []

    # Handle single ID
    if delete_params.id is not None:
        candidate = (
            db.query(GWCandidate).filter(GWCandidate.id == delete_params.id).first()
        )
        if not candidate:
            raise not_found_exception(
                f"No candidate found with 'id': {delete_params.id}"
            )

        if candidate.submitterid != user.id:
            raise permission_exception(
                "Error: Unauthorized. Unable to alter other user's records"
            )

        candidates_to_delete.append(candidate)

    # Handle multiple IDs
    elif delete_params.ids is not None:
        query_ids = delete_params.ids
        candidates = db.query(GWCandidate).filter(GWCandidate.id.in_(query_ids)).all()

        if len(candidates) == 0:
            raise not_found_exception("No candidates found with provided 'ids'")

        # Filter candidates the user is allowed to delete
        candidates_to_delete.extend([x for x in candidates if x.submitterid == user.id])
        if len(candidates_to_delete) < len(candidates):
            warnings.append(
                "Some entries were not deleted. You cannot delete candidates you didn't submit"
            )

    else:
        raise validation_exception(
            message="Missing required parameter",
            errors=["Either 'id' or 'ids' parameter is required"],
        )

    # Delete the candidates
    if len(candidates_to_delete):
        del_ids = []
        for ctd in candidates_to_delete:
            del_ids.append(ctd.id)
            db.delete(ctd)

        db.commit()

        return DeleteCandidateResponse(
            message=f"Successfully deleted {len(candidates_to_delete)} candidate(s)",
            deleted_ids=del_ids,
            warnings=warnings,
        )
