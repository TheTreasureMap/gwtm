from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Tuple
from datetime import datetime
from server.core.enums.instrument_type import instrument_type as instrument_type_enum

class InstrumentSchema(BaseModel):
    id: int
    instrument_name: str
    nickname: Optional[str] = None
    instrument_type: instrument_type_enum
    datecreated: Optional[datetime] = None
    submitterid: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)

    @field_validator("instrument_type", mode="before")
    def serialize_enum(cls, value):
        if isinstance(value, instrument_type_enum):
            return value.value  # Convert enum to its name (e.g., "photometric")
        return value

class InstrumentCreate(BaseModel):
    instrument_name: str
    nickname: Optional[str] = None
    instrument_type: instrument_type_enum

class InstrumentUpdate(BaseModel):
    instrument_name: Optional[str] = None
    nickname: Optional[str] = None
    instrument_type: Optional[instrument_type_enum] = None

class FootprintCCDSchema(BaseModel):
    id: int
    instrumentid: int
    footprint: Optional[str] = Field(None, description="WKT representation of the footprint")

    model_config = ConfigDict(from_attributes=True)

class FootprintCCDCreate(BaseModel):
    instrumentid: int
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
