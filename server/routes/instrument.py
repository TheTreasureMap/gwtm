from fastapi import APIRouter, Depends
from geoalchemy2 import WKBElement
from sqlalchemy.orm import Session
from typing import List, Optional
from shapely.wkb import loads as wkb_loads
import json
import datetime
from sqlalchemy import or_

from server.core.enums.instrument_type import instrument_type
from server.db.database import get_db
from server.db.models.instrument import Instrument, FootprintCCD
from server.db.models.pointing import Pointing
from server.schemas.instrument import (
    InstrumentSchema, 
    FootprintCCDSchema,
    InstrumentCreate,
    FootprintCCDCreate
)
from server.auth.auth import get_current_user
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception

router = APIRouter(tags=["instruments"])

@router.get("/instruments", response_model=List[InstrumentSchema])
async def get_instruments(
    id: Optional[int] = None,
    ids: Optional[str] = None,
    name: Optional[str] = None,
    names: Optional[str] = None,
    type: Optional[instrument_type] = None,
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

@router.get("/footprints", response_model=List[FootprintCCDSchema])
async def get_footprints(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get instrument footprints with optional filters.
    
    Parameters:
    - id: Filter by instrument ID
    - name: Filter by instrument name (fuzzy match)
    
    Returns a list of footprint objects
    """
    filter_conditions = []
    
    if id:
        filter_conditions.append(FootprintCCD.instrumentid == id)
    
    if name:
        filter_conditions.append(FootprintCCD.instrumentid == Instrument.id)
        
        or_conditions = []
        or_conditions.append(Instrument.instrument_name.contains(name.strip()))
        or_conditions.append(Instrument.nickname.contains(name.strip()))
        
        filter_conditions.append(or_(*or_conditions))
    
    footprints = db.query(FootprintCCD).filter(*filter_conditions).all()

    # Convert WKB to WKT for the `footprint` field
    for footprint in footprints:
        if isinstance(footprint.footprint, WKBElement):
            footprint.footprint = str(wkb_loads(bytes(footprint.footprint.data)))

    
    # FastAPI will automatically convert SQLAlchemy models to Pydantic models
    return footprints



@router.post("/instruments", response_model=InstrumentSchema)
async def create_instrument(
    instrument: InstrumentCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
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
        datecreated=datetime.datetime.now()
    )
    
    db.add(new_instrument)
    db.commit()
    db.refresh(new_instrument)
    
    return new_instrument

@router.post("/footprints", response_model=FootprintCCDSchema)
async def create_footprint(
    footprint: FootprintCCDCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Create a new footprint for an instrument.
    
    Parameters:
    - footprint: Footprint data
    
    Returns the created footprint
    """
    # Check if the instrument exists
    instrument = db.query(Instrument).filter(Instrument.id == footprint.instrumentid).first()
    if not instrument:
        raise not_found_exception(f"Instrument with ID {footprint.instrumentid} not found")
    
    # Check permissions (only the instrument submitter can add footprints)
    if instrument.submitterid != user.id:
        raise permission_exception("You don't have permission to add footprints to this instrument")
    
    # Create a new footprint
    new_footprint = FootprintCCD(
        instrumentid=footprint.instrumentid,
        footprint=footprint.footprint  # WKT format
    )

    db.add(new_footprint)
    db.commit()
    db.refresh(new_footprint)

    # Convert the footprint from WKB to WKT for the response
    if isinstance(new_footprint.footprint, WKBElement):
        new_footprint.footprint = str(wkb_loads(bytes(new_footprint.footprint.data)))

    return new_footprint
