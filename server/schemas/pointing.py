from pydantic import BaseModel, ConfigDict, model_validator, field_serializer, field_validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from server.core.enums import bandpass as bandpass_enum
from server.core.enums import depth_unit as depth_unit_enum
from server.core.enums.pointing_status import pointing_status as pointing_status_enum


class PointingBase(BaseModel):
    """Base schema for pointing data."""
    position: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    instrumentid: Optional[int] = None
    depth: Optional[float] = None
    depth_err: Optional[float] = None
    depth_unit: Optional[Union[depth_unit_enum, str]] = None
    band: Optional[Union[bandpass_enum, str]] = None
    pos_angle: Optional[float] = None
    time: Optional[datetime] = None
    status: Optional[Union[pointing_status_enum, str]] = "completed"
    central_wave: Optional[float] = None
    bandwidth: Optional[float] = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        if isinstance(value, str):
            try:
                return pointing_status_enum[value]
            except KeyError:
                # Return the string value if it's not a valid enum
                return value
        return value

    @field_validator("depth_unit", mode="before")
    @classmethod
    def validate_depth_unit(cls, value):
        if isinstance(value, str):
            try:
                return depth_unit_enum[value]
            except KeyError:
                # Return the string value if it's not a valid enum
                return value
        return value

    @field_validator("band", mode="before")
    @classmethod
    def validate_band(cls, value):
        if isinstance(value, str):
            try:
                return bandpass_enum[value]
            except KeyError:
                # Return the string value if it's not a valid enum
                return value
        return value

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            pointing_status_enum: lambda v: v.name if v else None,
            depth_unit_enum: lambda v: v.name if v else None,
            bandpass_enum: lambda v: v.name if v else None,
        }
    )


class PointingCreate(PointingBase):
    """Schema for creating a new pointing."""
    id: Optional[int] = None


class PointingResponse(BaseModel):
    """Schema for pointing creation response."""
    pointing_ids: List[int]
    ERRORS: List[Any] = []
    WARNINGS: List[Any] = []
    DOI: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PointingSchema(PointingBase):
    """Schema for returning a pointing."""
    id: int
    submitterid: Optional[int] = None
    datecreated: Optional[datetime] = None
    dateupdated: Optional[datetime] = None
    doi_url: Optional[str] = None
    doi_id: Optional[int] = None

    @field_serializer("status")
    def serialize_status(self, status):
        """Convert enum to string for JSON response."""
        if isinstance(status, pointing_status_enum):
            return status.name
        return status

    @field_serializer("depth_unit")
    def serialize_depth_unit(self, depth_unit):
        """Convert enum to string for JSON response."""
        if isinstance(depth_unit, depth_unit_enum):
            return depth_unit.name
        return depth_unit

    @field_serializer("band")
    def serialize_band(self, band):
        """Convert enum to string for JSON response."""
        if isinstance(band, bandpass_enum):
            return band.name
        return band

    model_config = ConfigDict(from_attributes=True)
