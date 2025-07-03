from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
    field_validator,
    field_serializer,
)
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from server.core.enums import Bandpass as bandpass_enum
from server.core.enums import DepthUnit as depth_unit_enum
from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum


class PointingBase(BaseModel):
    """Base schema for pointing data."""

    position: Optional[Union[str, Any]] = None  # Can be WKBElement or string
    ra: Optional[float] = None
    dec: Optional[float] = None
    instrumentid: Optional[int] = None
    depth: Optional[float] = None
    depth_err: Optional[float] = None
    depth_unit: Optional[Union[depth_unit_enum, str, int]] = None
    band: Optional[Union[bandpass_enum, str, int]] = None
    pos_angle: Optional[float] = None
    time: Optional[datetime] = None
    status: Optional[Union[pointing_status_enum, str, int]] = "completed"
    central_wave: Optional[float] = None
    bandwidth: Optional[float] = None

    # Serializers to convert enum values to string names
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

    @field_serializer("position")
    def serialize_position(self, position):
        """Convert WKBElement to string for JSON response."""
        if position and hasattr(position, "data"):
            import shapely.wkb

            try:
                geom = shapely.wkb.loads(bytes(position.data))
                return str(geom)
            except Exception:
                pass
        return position

    # Validators to convert string values to enum values
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
        elif isinstance(value, int):
            try:
                return depth_unit_enum(value)
            except ValueError:
                # Return the int value if it's not a valid enum
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
        elif isinstance(value, int):
            try:
                return bandpass_enum(value)
            except ValueError:
                # Return the int value if it's not a valid enum
                return value
        return value

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        json_encoders={
            pointing_status_enum: lambda v: v.name if v else None,
            depth_unit_enum: lambda v: v.name if v else None,
            bandpass_enum: lambda v: v.name if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        },
    )


class PointingResponse(BaseModel):
    """Schema for pointing creation response."""

    pointing_ids: List[int]
    ERRORS: List[Any] = []
    WARNINGS: List[Any] = []
    DOI: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PointingSchema(PointingBase):
    """Schema for returning a pointing."""

    id: Optional[int] = None
    submitterid: Optional[int] = None
    datecreated: Optional[datetime] = None
    dateupdated: Optional[datetime] = None
    doi_url: Optional[str] = None
    doi_id: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        json_encoders={
            pointing_status_enum: lambda v: v.name if v else None,
            depth_unit_enum: lambda v: v.name if v else None,
            bandpass_enum: lambda v: v.name if v else None,
            datetime: lambda v: v.isoformat() if v else None,
        },
    )


class PointingCreate(PointingBase):
    """Schema for creating a new pointing with comprehensive validation."""

    id: Optional[int] = Field(None, description="ID for updating an existing pointing")

    @model_validator(mode="after")
    def validate_pointing_data(self):
        """Comprehensive validation for pointing creation or update."""
        errors = []
        is_update = self.id is not None

        # For updates, we're more lenient with validation
        if not is_update:
            # Full validation for new pointings

            # Validate required fields based on status
            if self.status == pointing_status_enum.completed:
                if not self.depth:
                    errors.append("depth is required for completed observations")
                if not self.depth_unit:
                    errors.append("depth_unit is required for completed observations")
                if not self.band:
                    errors.append("band is required for completed observations")
                if not self.time:
                    errors.append("time is required for completed observations")

            elif self.status == pointing_status_enum.planned:
                if not self.time:
                    errors.append("time is required for planned observations")

            # Validate position (ra/dec or position string) - required for new pointings
            if not self.position and not (self.ra is not None and self.dec is not None):
                errors.append(
                    "Position information required (either position string or ra/dec coordinates)"
                )

        else:
            # For updates, only validate fields if they're being changed to completed status
            if self.status == pointing_status_enum.completed:
                # Only require these fields if they're not already set in the database
                # The service layer will handle checking existing values
                pass

        # Validate position format if provided as string (for both new and updates)
        if self.position and not (
            self.position
            and all(x in self.position for x in ["POINT", "(", ")", " "])
            and "," not in self.position
        ):
            errors.append(
                'Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type "POINT(RA DEC)"'
            )

        # Convert ra/dec to position if provided (for both new and updates)
        if self.ra is not None and self.dec is not None:
            if not isinstance(self.ra, (int, float)) or not isinstance(
                self.dec, (int, float)
            ):
                errors.append(
                    "Invalid position argument. Must be decimal format ra/RA, dec/DEC"
                )
            else:
                self.position = f"POINT({self.ra} {self.dec})"

        # Validate numeric fields (for both new and updates)
        if self.depth is not None and not isinstance(self.depth, (int, float)):
            errors.append("Invalid depth. Must be decimal")

        if self.depth_err is not None and not isinstance(self.depth_err, (int, float)):
            errors.append("Invalid depth_err. Must be decimal")

        if self.pos_angle is not None and not isinstance(self.pos_angle, (int, float)):
            errors.append("Invalid pos_angle. Must be decimal")

        if errors:
            raise ValueError("; ".join(errors))

        return self


class PointingCreateRequest(BaseModel):
    """Schema for the complete pointing creation request."""

    graceid: str = Field(..., description="Grace ID of the GW event")
    pointing: Optional[PointingCreate] = Field(
        None, description="Single pointing object"
    )
    pointings: Optional[List[PointingCreate]] = Field(
        None, description="List of pointing objects"
    )
    request_doi: Optional[bool] = Field(False, description="Whether to request a DOI")
    creators: Optional[List[Dict[str, str]]] = Field(
        None, description="List of creators for the DOI"
    )
    doi_group_id: Optional[int] = Field(None, description="DOI author group ID")
    doi_url: Optional[str] = Field(
        None, description="Optional DOI URL if already exists"
    )

    @model_validator(mode="after")
    def validate_request(self):
        """Validate the request has either pointing or pointings."""
        if not self.pointing and not self.pointings:
            raise ValueError("Either pointing or pointings must be provided")

        if self.pointing and self.pointings:
            raise ValueError("Cannot provide both pointing and pointings")

        # Validate DOI creators if request_doi is True
        if self.request_doi and self.creators:
            for creator in self.creators:
                if "name" not in creator or "affiliation" not in creator:
                    raise ValueError(
                        "name and affiliation are required for each creator in the list"
                    )

        return self


class PointingUpdate(BaseModel):
    """Schema for updating a pointing."""

    status: Union[pointing_status_enum, str] = Field(
        ..., description="New status for the pointings"
    )
    ids: List[int] = Field(..., description="List of pointing IDs to update")

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, value):
        if isinstance(value, str):
            try:
                return pointing_status_enum[value]
            except KeyError:
                raise ValueError(
                    f"Invalid status: {value}. Valid values are: {[s.name for s in pointing_status_enum]}"
                )
        return value

    @model_validator(mode="after")
    def validate_update(self):
        """Validate update request."""
        if not self.ids:
            raise ValueError("At least one pointing ID must be provided")

        # Currently only support cancelling
        if self.status != pointing_status_enum.cancelled:
            raise ValueError("Only 'cancelled' status updates are currently supported")

        return self


class CancelAllRequest(BaseModel):
    """Schema for cancelling all pointings."""

    graceid: str = Field(..., description="Grace ID of the GW event")
    instrumentid: int = Field(..., description="Instrument ID to cancel pointings for")


class DOIRequest(BaseModel):
    """Schema for requesting a DOI."""

    graceid: Optional[str] = Field(None, description="Grace ID of the GW event")
    id: Optional[int] = Field(None, description="Pointing ID")
    ids: Optional[List[int]] = Field(None, description="List of pointing IDs")
    doi_group_id: Optional[str] = Field(None, description="DOI author group ID")
    creators: Optional[List[Dict[str, str]]] = Field(
        None, description="List of creators for the DOI"
    )
    doi_url: Optional[str] = Field(
        None, description="Optional DOI URL if already exists"
    )

    @model_validator(mode="after")
    def validate_doi_request(self):
        """Validate DOI request parameters."""
        if not self.graceid and not self.id and not self.ids:
            raise ValueError("Please provide either graceid, id, or ids parameter")

        if self.creators:
            for creator in self.creators:
                if "name" not in creator or "affiliation" not in creator:
                    raise ValueError(
                        "name and affiliation are required for each creator in the list"
                    )

        return self
