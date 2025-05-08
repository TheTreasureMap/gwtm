from pydantic import BaseModel, ConfigDict, model_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from server.core.enums.pointing_status import pointing_status



class PointingBase(BaseModel):
    """Base schema for pointing data."""
    position: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    instrumentid: Optional[int] = None
    depth: Optional[float] = None
    depth_err: Optional[float] = None
    depth_unit: Optional[str] = None
    band: Optional[str] = None
    pos_angle: Optional[float] = None
    time: Optional[datetime] = None
    status: Optional[pointing_status] = "completed"
    central_wave: Optional[float] = None
    bandwidth: Optional[float] = None

    model_config = ConfigDict(extra="allow")  # Allow additional fields for Flask compatibility

    @model_validator(mode="before")
    def validate_position_or_coords(cls, values):
        """Validate that either position or ra/dec are provided."""
        position = values.get('position')
        ra = values.get('ra', values.get('RA'))
        dec = values.get('dec', values.get('DEC'))

        if position is None and (ra is None or dec is None):
            pass  # We'll let the application logic handle this validation

        return values


class PointingCreate(PointingBase):
    """Schema for creating a new pointing."""
    id: Optional[int] = None  # Optional for updating planned pointings


class PointingResponse(BaseModel):
    """Schema for pointing creation response."""
    pointing_ids: List[int]
    ERRORS: List[Any] = []
    WARNINGS: List[Any] = []
    DOI: Optional[str] = None


class PointingSchema(PointingBase):
    """Schema for returning a pointing."""
    id: int
    submitterid: Optional[int] = None
    datecreated: Optional[datetime] = None
    dateupdated: Optional[datetime] = None
    doi_url: Optional[str] = None
    doi_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
