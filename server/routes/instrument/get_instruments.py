"""Get instruments endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import json

from server.db.database import get_db
from server.db.models.instrument import Instrument
from server.db.models.pointing import Pointing
from server.schemas.instrument import InstrumentSchema
from server.auth.auth import get_current_user
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
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get instruments with optional filters.
    
    Parameters:
    - id: Filter by instrument ID
    - ids: Filter by list of instrument IDs
    - name: Filter by instrument name (fuzzy match)
    - names: Filter by list of instrument names (fuzzy match)
    - type: Filter by instrument type
    
    Returns a list of instrument objects
    """
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
        filter_conditions.append(Instrument.instrument_name.contains(name))
    
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
            raise validation_exception("Invalid names format. Must be a JSON array.")
    
    if type:
        filter_conditions.append(Instrument.instrument_type == type)
    
    instruments = db.query(Instrument).filter(*filter_conditions).all()
    
    # FastAPI will automatically convert SQLAlchemy models to Pydantic models
    return instruments
