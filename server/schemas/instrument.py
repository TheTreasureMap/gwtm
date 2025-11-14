from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum
from server.core.enums.instrumenttype import InstrumentType as instrument_type_enum


class FootprintType(str, Enum):
    """Valid footprint shape types."""
    rectangular = "Rectangular"
    circular = "Circular"
    polygon = "Polygon"


class FootprintUnit(str, Enum):
    """Valid footprint units."""
    deg = "deg"
    arcmin = "arcmin"
    arcsec = "arcsec"


class InstrumentSchema(BaseModel):
    """Schema for returning an instrument."""

    id: int = Field(..., description="Unique identifier for the instrument")
    instrument_name: str = Field(..., description="Name of the instrument")
    nickname: Optional[str] = Field(
        None, description="Nickname or short name for the instrument"
    )
    instrument_type: instrument_type_enum = Field(
        ..., description="Type of the instrument"
    )
    datecreated: Optional[datetime] = Field(
        None, description="Date when the instrument was created"
    )
    submitterid: Optional[int] = Field(
        None, description="ID of the user who submitted the instrument"
    )
    num_pointings: Optional[int] = Field(
        None,
        description="Number of completed pointings (only included when reporting_only=true)",
    )

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)

    @field_validator("instrument_type", mode="before")
    def serialize_enum(cls, value):
        if isinstance(value, instrument_type_enum):
            return value.value  # Convert enum to its name (e.g., "photometric")
        return value


class InstrumentCreate(BaseModel):
    """Schema for creating a new instrument with footprint."""

    instrument_name: str = Field(..., description="Name of the instrument")
    nickname: Optional[str] = Field(
        None, description="Nickname or short name for the instrument"
    )
    instrument_type: instrument_type_enum = Field(
        ..., description="Type of the instrument"
    )
    
    # Footprint fields
    footprint_type: FootprintType = Field(
        ..., description="Type of footprint shape (Rectangular, Circular, Polygon)"
    )
    unit: FootprintUnit = Field(
        ..., description="Unit for footprint dimensions (deg, arcmin, arcsec)"
    )
    
    # Rectangular footprint fields
    height: Optional[float] = Field(
        None, description="Height for rectangular footprint"
    )
    width: Optional[float] = Field(
        None, description="Width for rectangular footprint"
    )
    
    # Circular footprint fields
    radius: Optional[float] = Field(
        None, description="Radius for circular footprint"
    )
    
    # Polygon footprint field
    polygon: Optional[str] = Field(
        None, description="Polygon coordinates as text (supports multi-polygon format)"
    )

    @field_validator("height", "width", mode="before")
    def validate_rectangular_fields(cls, value, info):
        """Validate rectangular footprint fields."""
        if info.data.get("footprint_type") == FootprintType.rectangular:
            if value is None:
                raise ValueError("Height and width are required for rectangular footprint")
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError("Height and width must be positive numbers")
        return value
    
    @field_validator("radius", mode="before")
    def validate_circular_fields(cls, value, info):
        """Validate circular footprint fields."""
        if info.data.get("footprint_type") == FootprintType.circular:
            if value is None:
                raise ValueError("Radius is required for circular footprint")
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError("Radius must be a positive number")
        return value
    
    @field_validator("polygon", mode="before")
    def validate_polygon_fields(cls, value, info):
        """Validate polygon footprint fields."""
        if info.data.get("footprint_type") == FootprintType.polygon:
            if not value:
                raise ValueError("Polygon coordinates are required for polygon footprint")
        return value


class InstrumentCreateResponse(BaseModel):
    """Response schema for instrument creation."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Success or error message")
    instrument: Optional[InstrumentSchema] = Field(
        None, description="Created instrument (if successful)"
    )
    errors: List[str] = Field(
        default_factory=list, description="List of validation errors (if any)"
    )


class InstrumentUpdate(BaseModel):
    """Schema for updating an instrument."""

    instrument_name: Optional[str] = Field(
        None, description="Updated name of the instrument"
    )
    nickname: Optional[str] = Field(
        None, description="Updated nickname or short name for the instrument"
    )
    instrument_type: Optional[instrument_type_enum] = Field(
        None, description="Updated type of the instrument"
    )


class FootprintCCDSchema(BaseModel):
    """Schema for returning a footprint CCD."""

    id: int = Field(..., description="Unique identifier for the footprint")
    instrumentid: int = Field(..., description="ID of the associated instrument")
    footprint: Optional[str] = Field(
        None, description="WKT representation of the footprint"
    )

    model_config = ConfigDict(from_attributes=True)


class FootprintCCDCreate(BaseModel):
    """Schema for creating a new footprint CCD."""

    instrumentid: int = Field(..., description="ID of the associated instrument")
    footprint: str = Field(..., description="WKT representation of the footprint")

    @field_validator("footprint")
    def validate_footprint(cls, value):
        if value:
            try:
                from shapely.wkt import loads

                loads(value)  # Attempt to parse the WKT
            except Exception as e:
                raise ValueError(f"Invalid WKT format: {e}")
        return value
