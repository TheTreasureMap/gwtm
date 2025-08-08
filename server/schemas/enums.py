"""Schemas for enum endpoints."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class EnumOption(BaseModel):
    """Single enum option schema."""

    name: str = Field(..., description="Human-readable name")
    value: str = Field(..., description="Enum value to use in API calls")
    description: Optional[str] = Field(None, description="Optional description")


class EnumResponse(BaseModel):
    """Response schema for enum endpoints."""

    enum_type: str = Field(
        ..., description="Type of enum (e.g., 'bandpass', 'depth_unit')"
    )
    options: List[EnumOption] = Field(..., description="List of available options")


class AllEnumsResponse(BaseModel):
    """Response schema for all enums endpoint."""

    enums: Dict[str, List[EnumOption]] = Field(
        ..., description="Dictionary of all enum types and their options"
    )
