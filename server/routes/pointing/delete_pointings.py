"""Delete pointings endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.schemas.pointing import PointingDeleteRequest
from server.auth.auth import get_current_user, is_admin_user
from server.utils.error_handling import not_found_exception, validation_exception

router = APIRouter(tags=["pointings"])


@router.delete("/pointings")
async def delete_pointings(
    request: PointingDeleteRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Delete pointings by ID.

    Users may only delete their own pointings. Admins may delete any pointing.
    Associated pointing_event rows are also removed.
    """
    try:
        admin = is_admin_user(user, db)

        query = db.query(Pointing.id).filter(Pointing.id.in_(request.ids))
        if not admin:
            query = query.filter(Pointing.submitterid == user.id)

        deleted_ids = sorted(row.id for row in query.all())
        if not deleted_ids:
            raise not_found_exception("No matching pointings found for the given IDs.")

        db.query(PointingEvent).filter(
            PointingEvent.pointingid.in_(deleted_ids)
        ).delete(synchronize_session=False)

        db.query(Pointing).filter(
            Pointing.id.in_(deleted_ids)
        ).delete(synchronize_session=False)

        db.commit()

        failed_ids = sorted(set(request.ids) - set(deleted_ids))
        return {
            "message": f"Deleted {len(deleted_ids)} of {len(request.ids)} pointing(s).",
            "deleted_ids": deleted_ids,
            "failed_ids": failed_ids,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise validation_exception(message="Invalid request", errors=[str(e)])
