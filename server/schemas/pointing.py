from pydantic import BaseModel, ConfigDict, model_validator, field_serializer, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from server.core.enums import bandpass as bandpass_ehum
from server.core.enums import depth_unit as depth_unit_ehum
from server.core.enums.pointing_status import pointing_status as pointing_status_ehum



class PointingBase(BaseModel):
    """Base schema for pointing data."""
    position: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    instrumentid: Optional[int] = None
    depth: Optional[float] = None
    depth_err: Optional[float] = None
    depth_unit: Optional[depth_unit_ehum] = None
    band: Optional[bandpass_ehum] = None
    pos_angle: Optional[float] = None
    time: Optional[datetime] = None
    status: Optional[pointing_status_ehum] = "completed"
    central_wave: Optional[float] = None
    bandwidth: Optional[float] = None

    @field_validator("status", mode="before")
    def validate_status(cls, value):
        if isinstance(value, str):
            try:
                return pointing_status_ehum[value]  # Convert string to enum
            except KeyError:
                raise ValueError(f"Invalid status value: {value}")
        return value

    @field_serializer("status")
    def serialize_status(self, status):
        """Serialize the status field to return its enum value as a string."""
        return status.name if status else None

    @field_serializer("band")
    def serialize_band(self, band: Optional[bandpass_ehum]) -> Optional[str]:
        """Serialize the band field to return its enum value as a string."""
        return band.name if band else None

    @field_serializer("depth_unit")
    def serialize_depth_unit(self, depth_unit: Optional[depth_unit_ehum]) -> Optional[str]:
        if depth_unit is None:
            return None
        try:
            return depth_unit.name
        except AttributeError as e:
            print(f"Debug: Invalid depth_unit value: {depth_unit}")
            raise ValueError(f"Invalid depth_unit value: {depth_unit}") from e

    @field_validator("depth_unit", mode="before")
    def validate_depth_unit(cls, value):
        if isinstance(value, str):
            return depth_unit_ehum[value]  # Convert string to enum
        return value

    @field_validator("band", mode="before")
    def validate_band(cls, value):
        if isinstance(value, str):
            return bandpass_ehum[value]  # Convert string to enum
        return value

    model_config = ConfigDict(extra="allow")  # Allow additional fields for Flask compatibility

    def validate_position_or_coords(cls, values):
        """Validate that either position or ra/dec are provided."""
        position = values.position
        ra = values.ra
        dec = values.dec

        if position is None and (ra is None or dec is None):
            raise ValueError("Either 'position' or both 'ra' and 'dec' must be provided.")

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
