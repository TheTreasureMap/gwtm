from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Tuple
from datetime import datetime
from server.core.enums.instrument_type import instrument_type as instrument_type_enum

class InstrumentSchema(BaseModel):
    """Schema for returning an instrument."""
    id: int = Field(..., description="Unique identifier for the instrument")
    instrument_name: str = Field(..., description="Name of the instrument")
    nickname: Optional[str] = Field(None, description="Nickname or short name for the instrument")
    instrument_type: instrument_type_enum = Field(..., description="Type of the instrument")
    datecreated: Optional[datetime] = Field(None, description="Date when the instrument was created")
    submitterid: Optional[int] = Field(None, description="ID of the user who submitted the instrument")

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)

    @field_validator("instrument_type", mode="before")
    def serialize_enum(cls, value):
        if isinstance(value, instrument_type_enum):
            return value.value  # Convert enum to its name (e.g., "photometric")
        return value

class InstrumentCreate(BaseModel):
    """Schema for creating a new instrument."""
    instrument_name: str = Field(..., description="Name of the instrument")
    nickname: Optional[str] = Field(None, description="Nickname or short name for the instrument")
    instrument_type: instrument_type_enum = Field(..., description="Type of the instrument")

class InstrumentUpdate(BaseModel):
    """Schema for updating an instrument."""
    instrument_name: Optional[str] = Field(None, description="Updated name of the instrument")
    nickname: Optional[str] = Field(None, description="Updated nickname or short name for the instrument")
    instrument_type: Optional[instrument_type_enum] = Field(None, description="Updated type of the instrument")

class FootprintCCDSchema(BaseModel):
    """Schema for returning a footprint CCD."""
    id: int = Field(..., description="Unique identifier for the footprint")
    instrumentid: int = Field(..., description="ID of the associated instrument")
    footprint: Optional[str] = Field(None, description="WKT representation of the footprint")

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
