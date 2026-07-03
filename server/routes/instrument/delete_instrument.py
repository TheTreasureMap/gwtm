"""Delete instrument endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.instrument import Instrument, FootprintCCD
from server.db.models.pointing import Pointing
from server.schemas.instrument import DeleteInstrumentResponse
from server.auth.auth import get_current_user
from server.routes.event.utils import is_admin
from server.utils.error_handling import (
    not_found_exception,
    permission_exception,
    conflict_exception,
)

router = APIRouter(tags=["instruments"])


@router.delete("/instruments/{instrument_id}", response_model=DeleteInstrumentResponse)
async def delete_instrument(
    instrument_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete an instrument together with its footprint CCDs.

    Only the instrument's submitter or an admin may delete it. Deletion is
    refused while any pointing still references the instrument, since those
    observation records would otherwise point at a missing instrument.
    """
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise not_found_exception(f"No instrument found with 'id': {instrument_id}")

    if instrument.submitterid != user.id and not is_admin(user, db):
        raise permission_exception(
            "Error: Unauthorized. Unable to alter other user's records"
        )

    pointing_count = (
        db.query(Pointing).filter(Pointing.instrumentid == instrument_id).count()
    )
    if pointing_count:
        raise conflict_exception(
            f"Instrument {instrument_id} is referenced by {pointing_count} "
            "pointing(s) and cannot be deleted."
        )

    deleted_footprints = (
        db.query(FootprintCCD)
        .filter(FootprintCCD.instrumentid == instrument_id)
        .delete()
    )
    db.delete(instrument)
    db.commit()

    return DeleteInstrumentResponse(
        message=f"Successfully deleted instrument {instrument_id}",
        deleted_id=instrument_id,
        deleted_footprints=deleted_footprints,
    )
