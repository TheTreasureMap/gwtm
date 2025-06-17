"""Update pointings endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.schemas.pointing import PointingUpdate
from server.auth.auth import get_current_user
from server.utils.error_handling import validation_exception
from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum

router = APIRouter(tags=["pointings"])


@router.post("/update_pointings")
async def update_pointings(
        update_pointing: PointingUpdate,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Update the status of planned pointings.

    Parameters:
    - status: The new status for the pointings (only "cancelled" is currently supported)
    - ids: List of pointing IDs to update

    Returns:
    - Message with the number of updated pointings
    """
    try:
        # Add a filter to ensure user can only update their own pointings
        pointings = db.query(Pointing).filter(
            Pointing.id.in_(update_pointing.ids),
            Pointing.submitterid == user.id,
            Pointing.status == pointing_status_enum.planned  # Only planned pointings can be cancelled
        ).all()

        for pointing in pointings:
            pointing.status = update_pointing.status
            pointing.dateupdated = datetime.now()

        db.commit()
        return {"message": f"Updated {len(pointings)} pointings successfully."}
    except Exception as e:
        db.rollback()
        raise validation_exception(message="Invalid request", errors=[str(e)])
