"""Create instrument endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import datetime

from server.db.database import get_db
from server.db.models.instrument import Instrument
from server.schemas.instrument import InstrumentCreate, InstrumentSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["instruments"])


@router.post("/instruments", response_model=InstrumentSchema)
async def create_instrument(
    instrument: InstrumentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create a new instrument.

    Parameters:
    - instrument: Instrument data

    Returns the created instrument
    """
    # Create a new instrument
    new_instrument = Instrument(
        instrument_name=instrument.instrument_name,
        nickname=instrument.nickname,
        instrument_type=instrument.instrument_type,
        submitterid=user.id,
        datecreated=datetime.datetime.now(),
    )

    db.add(new_instrument)
    db.commit()
    db.refresh(new_instrument)

    return new_instrument
