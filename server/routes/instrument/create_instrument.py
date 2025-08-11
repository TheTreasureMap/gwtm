"""Create instrument endpoint with footprint support."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import datetime
from typing import List

from server.db.database import get_db
from server.db.models.instrument import Instrument, FootprintCCD
from server.schemas.instrument import InstrumentCreate, InstrumentCreateResponse, InstrumentSchema
from server.auth.auth import get_current_user
from server.utils.footprint_processing import (
    get_scale_factor,
    create_rectangular_footprint,
    create_circular_footprint,
    parse_multi_polygon,
    create_geography_from_vertices,
    validate_footprint_data
)

router = APIRouter(tags=["instruments"])


@router.post("/instruments", response_model=InstrumentCreateResponse)
async def create_instrument(
    instrument: InstrumentCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create a new instrument with footprint.

    Parameters:
    - instrument: Instrument data including footprint information

    Returns success/error response with created instrument
    """
    try:
        # Validate footprint data
        is_valid, validation_errors = validate_footprint_data(
            instrument.footprint_type.value,
            height=instrument.height,
            width=instrument.width,
            radius=instrument.radius,
            polygon=instrument.polygon
        )
        
        if not is_valid:
            return InstrumentCreateResponse(
                success=False,
                message="Validation failed",
                errors=validation_errors
            )
        
        # Get scale factor for unit conversion
        scale = get_scale_factor(instrument.unit.value)
        
        # Process footprint based on type
        footprint_polygons = []
        processing_errors = []
        
        if instrument.footprint_type.value == "Rectangular":
            vertices = create_rectangular_footprint(instrument.height, instrument.width, scale)
            footprint_polygons.append(vertices)
            
        elif instrument.footprint_type.value == "Circular":
            vertices = create_circular_footprint(instrument.radius, scale)
            footprint_polygons.append(vertices)
            
        elif instrument.footprint_type.value == "Polygon":
            polygons, poly_errors = parse_multi_polygon(instrument.polygon, scale)
            if poly_errors:
                processing_errors.extend(poly_errors)
            else:
                footprint_polygons.extend(polygons)
        
        if processing_errors:
            return InstrumentCreateResponse(
                success=False,
                message="Footprint processing failed",
                errors=processing_errors
            )
        
        if not footprint_polygons:
            return InstrumentCreateResponse(
                success=False,
                message="No valid footprint polygons created",
                errors=["Failed to generate footprint geometry"]
            )
        
        # Create the instrument record
        new_instrument = Instrument(
            instrument_name=instrument.instrument_name,
            nickname=instrument.nickname,
            instrument_type=instrument.instrument_type,
            submitterid=user.id,
            datecreated=datetime.datetime.now(),
        )
        
        db.add(new_instrument)
        db.flush()  # Get the ID but don't commit yet
        
        # Create footprint records
        footprint_ccds = []
        for vertices in footprint_polygons:
            try:
                footprint_geog = create_geography_from_vertices(vertices)
                footprint_ccd = FootprintCCD(
                    instrumentid=new_instrument.id,
                    footprint=footprint_geog
                )
                footprint_ccds.append(footprint_ccd)
                db.add(footprint_ccd)
            except Exception as e:
                processing_errors.append(f"Error creating footprint geometry: {str(e)}")
        
        if processing_errors:
            db.rollback()
            return InstrumentCreateResponse(
                success=False,
                message="Footprint creation failed", 
                errors=processing_errors
            )
        
        # Commit everything
        db.commit()
        db.refresh(new_instrument)
        
        # Create response with the full instrument data
        instrument_schema = InstrumentSchema.model_validate(new_instrument)
        
        return InstrumentCreateResponse(
            success=True,
            message=f"Successfully created instrument with ID {new_instrument.id}",
            instrument=instrument_schema
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return InstrumentCreateResponse(
            success=False,
            message="Internal server error",
            errors=[f"Unexpected error: {str(e)}"]
        )
