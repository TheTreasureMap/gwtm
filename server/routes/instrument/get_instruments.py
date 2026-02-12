"""Get instruments endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import json

from server.db.database import get_db
from server.db.models.instrument import Instrument
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.schemas.instrument import InstrumentSchema
from server.core.enums.pointingstatus import PointingStatus
from server.utils.error_handling import validation_exception
from server.core.enums.instrumenttype import InstrumentType

router = APIRouter(tags=["instruments"])


@router.get("/instruments", response_model=List[InstrumentSchema])
async def get_instruments(
    id: Optional[int] = None,
    ids: Optional[str] = None,
    name: Optional[str] = None,
    names: Optional[str] = None,
    type: Optional[InstrumentType] = None,
    reporting_only: Optional[bool] = False,
    db: Session = Depends(get_db),
):
    """
    Get instruments with optional filters.

    Parameters:
    - id: Filter by instrument ID
    - ids: Filter by list of instrument IDs
    - name: Filter by instrument name (fuzzy match)
    - names: Filter by list of instrument names (fuzzy match)
    - type: Filter by instrument type
    - reporting_only: If true, only return instruments with completed pointings and include pointing counts

    Returns a list of instrument objects
    """
    if reporting_only:
        # Special query for reporting instruments (matching Flask logic)
        query = (
            db.query(
                Instrument.id,
                Instrument.instrument_name,
                Instrument.nickname,
                Instrument.instrument_type,
                Instrument.datecreated,
                Instrument.submitterid,
                func.count(Pointing.id).label("num_pointings"),
            )
            .join(Pointing, Instrument.id == Pointing.instrumentid)
            .join(PointingEvent, PointingEvent.pointingid == Pointing.id)
            .filter(Pointing.status == PointingStatus.completed)
            .group_by(
                Instrument.id,
                Instrument.instrument_name,
                Instrument.nickname,
                Instrument.instrument_type,
                Instrument.datecreated,
                Instrument.submitterid,
            )
            .order_by(func.count(Pointing.id).desc())
        )

        results = query.all()

        # Convert to InstrumentSchema objects with num_pointings
        instruments = []
        for result in results:
            instrument_dict = {
                "id": result.id,
                "instrument_name": result.instrument_name,
                "nickname": result.nickname,
                "instrument_type": result.instrument_type,
                "datecreated": result.datecreated,
                "submitterid": result.submitterid,
                "num_pointings": result.num_pointings,
            }
            instruments.append(InstrumentSchema(**instrument_dict))

        return instruments

    else:
        # Original query logic for regular instrument listing
        filter_conditions = []

        if id:
            filter_conditions.append(Instrument.id == id)

        if ids:
            try:
                if isinstance(ids, str):
                    ids_list = json.loads(ids)
                else:
                    ids_list = ids
                filter_conditions.append(Instrument.id.in_(ids_list))
            except:
                raise validation_exception("Invalid ids format. Must be a JSON array.")

        if name:
            # Case-insensitive partial match in both name and nickname fields
            # This enhances Flask's behavior by also searching nicknames
            filter_conditions.append(
                or_(
                    Instrument.instrument_name.ilike(f"%{name}%"),
                    Instrument.nickname.ilike(f"%{name}%"),
                )
            )

        if names:
            try:
                if isinstance(names, str):
                    insts = json.loads(names)
                else:
                    insts = names

                or_conditions = []
                for i in insts:
                    or_conditions.append(Instrument.instrument_name.contains(i.strip()))

                filter_conditions.append(or_(*or_conditions))
                filter_conditions.append(Instrument.id == Pointing.instrumentid)
            except:
                raise validation_exception(
                    "Invalid names format. Must be a JSON array."
                )

        if type:
            filter_conditions.append(Instrument.instrument_type == type)

        instruments = db.query(Instrument).filter(*filter_conditions).all()

        # FastAPI will automatically convert SQLAlchemy models to Pydantic models
        return instruments
