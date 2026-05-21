"""PUT pointing endpoint — update any field on an existing pointing."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.schemas.pointing import PointingBase
from server.auth.auth import get_current_user, is_admin_user
from server.utils.error_handling import not_found_exception, validation_exception

router = APIRouter(tags=["pointings"])

# Fields from PointingBase that are allowed to be updated on an existing pointing.
# instrumentid is intentionally excluded — it is fixed at submission time.
# position is handled separately via ra/dec.
_UPDATABLE_FIELDS = frozenset({
    "status", "time", "depth", "depth_err", "depth_unit",
    "band", "pos_angle", "central_wave", "bandwidth",
})


@router.put("/pointings/{pointing_id}")
async def put_pointing(
    pointing_id: int,
    update: PointingBase,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Update fields on an existing pointing.

    Users may only update their own pointings. Admins may update any pointing.
    Only fields present in the request body are changed.
    """
    try:
        admin = is_admin_user(user, db)

        query = db.query(Pointing).filter(Pointing.id == pointing_id)
        if not admin:
            query = query.filter(Pointing.submitterid == user.id)

        pointing = query.first()
        if pointing is None:
            raise not_found_exception(
                f"Pointing {pointing_id} not found or not owned by user."
            )

        for field in update.model_dump(exclude_unset=True).keys() & _UPDATABLE_FIELDS:
            setattr(pointing, field, getattr(update, field))

        if update.ra is not None and update.dec is not None:
            pointing.position = f"POINT({update.ra} {update.dec})"

        pointing.dateupdated = datetime.now()
        db.commit()

        return {"message": f"Updated pointing {pointing_id} successfully."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise validation_exception(message="Invalid request", errors=[str(e)])
