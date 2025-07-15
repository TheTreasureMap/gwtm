from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Any, Literal, Dict, Union
from datetime import datetime
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated
from server.core.enums.depthunit import DepthUnit as depth_unit_enum


class CandidateSchema(BaseModel):
    id: int
    graceid: str
    submitterid: int
    candidate_name: str
    datecreated: Optional[datetime] = None
    tns_name: Optional[str] = None
    tns_url: Optional[str] = None
    position: Annotated[str, WKBElement] = Field(
        None, description="WKT representation of the position"
    )
    discovery_date: Optional[datetime] = None
    discovery_magnitude: Optional[float] = None
    magnitude_central_wave: Optional[float] = None
    magnitude_bandwidth: Optional[float] = None
    magnitude_unit: Optional[str] = None
    magnitude_bandpass: Optional[str] = None
    associated_galaxy: Optional[str] = None
    associated_galaxy_redshift: Optional[float] = None
    associated_galaxy_distance: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class GetCandidateQueryParams(BaseModel):
    id: Optional[int] = Field(None, description="Filter by candidate ID")
    ids: Optional[List[int]] = Field(
        None, description="Filter by a list of candidate IDs"
    )
    graceid: Optional[str] = Field(None, description="Filter by Grace ID")
    userid: Optional[int] = Field(None, description="Filter by user ID")
    submitted_date_after: Optional[datetime] = Field(
        None, description="Filter by submission date after this timestamp"
    )
    submitted_date_before: Optional[datetime] = Field(
        None, description="Filter by submission date before this timestamp"
    )
    discovery_magnitude_gt: Optional[float] = Field(
        None, description="Filter by discovery magnitude greater than this value"
    )
    discovery_magnitude_lt: Optional[float] = Field(
        None, description="Filter by discovery magnitude less than this value"
    )
    discovery_date_after: Optional[datetime] = Field(
        None, description="Filter by discovery date after this timestamp"
    )
    discovery_date_before: Optional[datetime] = Field(
        None, description="Filter by discovery date before this timestamp"
    )
    associated_galaxy_name: Optional[str] = Field(
        None, description="Filter by associated galaxy name"
    )
    associated_galaxy_redshift_gt: Optional[float] = Field(
        None, description="Filter by associated galaxy redshift greater than this value"
    )
    associated_galaxy_redshift_lt: Optional[float] = Field(
        None, description="Filter by associated galaxy redshift less than this value"
    )
    associated_galaxy_distance_gt: Optional[float] = Field(
        None, description="Filter by associated galaxy distance greater than this value"
    )
    associated_galaxy_distance_lt: Optional[float] = Field(
        None, description="Filter by associated galaxy distance less than this value"
    )


class CandidateRequest(BaseModel):
    """Single candidate submission model"""

    candidate_name: str
    position: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    tns_name: Optional[str] = None
    tns_url: Optional[str] = None
    discovery_date: str
    discovery_magnitude: float
    magnitude_unit: Union[depth_unit_enum, str, int]
    magnitude_bandpass: Optional[str] = None
    magnitude_central_wave: Optional[float] = None
    magnitude_bandwidth: Optional[float] = None
    wavelength_regime: Optional[List[float]] = None
    wavelength_unit: Optional[str] = None
    frequency_regime: Optional[List[float]] = None
    frequency_unit: Optional[str] = None
    energy_regime: Optional[List[float]] = None
    energy_unit: Optional[str] = None
    associated_galaxy: Optional[str] = None
    associated_galaxy_redshift: Optional[float] = None
    associated_galaxy_distance: Optional[float] = None

    @field_validator("discovery_date")
    def validate_discovery_date(cls, value):
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(
                "Invalid discovery_date format. Must be a valid ISO 8601 datetime string."
            )
        return value

    @field_validator("magnitude_unit", mode="before")
    @classmethod
    def validate_magnitude_unit(cls, value):
        """
        Validate magnitude unit, accepting both string and enum values.

        Args:
            value: Input magnitude unit (string or enum)

        Returns:
            depth_unit_enum: Validated enum value

        Raises:
            ValueError if the input is not a valid magnitude unit
        """
        if isinstance(value, depth_unit_enum):
            return value

        if isinstance(value, str):
            try:
                # Try converting string to enum by name
                return depth_unit_enum[value]
            except KeyError:
                # If name lookup fails, check if it can be converted from integer
                try:
                    return depth_unit_enum(int(value))
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Invalid magnitude unit: {value}. "
                        f"Must be one of {list(depth_unit_enum.__members__.keys())}"
                    )

        if isinstance(value, int):
            try:
                return depth_unit_enum(value)
            except ValueError:
                raise ValueError(f"Invalid magnitude unit value: {value}")

        raise ValueError(f"Invalid magnitude unit type: {type(value)}")

    @model_validator(mode="after")
    def validate_position_data(self):
        ra_dec_provided = sum([self.ra is not None, self.dec is not None]) > 0
        position_provided = self.position is not None
        if ra_dec_provided or position_provided:
            return self
        else:
            raise ValueError("Either position or both ra and dec must be provided")

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={depth_unit_enum: lambda v: v.name if v else None},
    )


class PostCandidateRequest(BaseModel):
    """Main request model with either single candidate or multiple candidates"""

    graceid: str
    candidate: Optional[CandidateRequest] = None
    candidates: Optional[List[CandidateRequest]] = None

    @model_validator(mode="after")
    def validate_exactly_one_candidate_field(self):
        fields_provided = sum(
            [
                self.candidate is not None,
                self.candidates is not None and len(self.candidates) > 0,
            ]
        )

        if fields_provided == 0:
            raise ValueError("Must provide either 'candidate' or 'candidates'")
        elif fields_provided > 1:
            raise ValueError("Cannot provide both 'candidate' and 'candidates'")

        return self


class CandidateResponse(BaseModel):
    """Response model matching the Flask API format"""

    candidate_ids: List[int]
    ERRORS: List[List[Any]]
    WARNINGS: List[List[Any]]


class CandidateUpdateField(BaseModel):
    """Fields that can be updated for a candidate"""

    graceid: Optional[str] = None
    candidate_name: Optional[str] = None
    tns_name: Optional[str] = None
    tns_url: Optional[str] = None
    position: Optional[str] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    discovery_date: Optional[str] = None
    discovery_magnitude: Optional[float] = None
    magnitude_central_wave: Optional[float] = None
    magnitude_bandwidth: Optional[float] = None
    magnitude_unit: Optional[str] = None
    magnitude_bandpass: Optional[str] = None
    associated_galaxy: Optional[str] = None
    associated_galaxy_redshift: Optional[float] = None
    associated_galaxy_distance: Optional[float] = None
    wavelength_regime: Optional[List[float]] = None
    wavelength_unit: Optional[str] = None
    frequency_regime: Optional[List[float]] = None
    frequency_unit: Optional[str] = None
    energy_regime: Optional[List[float]] = None
    energy_unit: Optional[str] = None

    @field_validator("discovery_date")
    def validate_discovery_date(cls, value):
        if value is not None:
            try:
                datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(
                    "discovery_date must be a valid ISO 8601 datetime string"
                )
        return value


class PutCandidateRequest(BaseModel):
    """Request model for updating a candidate"""

    id: int
    candidate: CandidateUpdateField


class PutCandidateSuccessResponse(BaseModel):
    """Success response model"""

    message: Literal["success"]
    candidate: Dict[str, Any]


class PutCandidateFailureResponse(BaseModel):
    """Failure response model"""

    message: Literal["failure"]
    errors: List[Any]


# Union type for response
PutCandidateResponse = Union[PutCandidateSuccessResponse, PutCandidateFailureResponse]


class DeleteCandidateResponse(BaseModel):
    """Response model for successful delete operation"""

    message: str
    deleted_ids: Optional[List[int]] = []
    warnings: Optional[List[str]] = []


# You can add this to your candidate.py schemas file
class DeleteCandidateParams(BaseModel):
    """
    Parameters for deleting candidates.
    Either id or ids must be provided.
    """

    id: Optional[int] = None
    ids: Optional[List[int]] = None


# Base schema with common fields
class GWCandidateBase(BaseModel):
    """Base schema for GW candidate data."""

    graceid: str = Field(..., description="Grace ID of the GW event")
    candidate_name: str = Field(..., description="Name of the candidate")
    submitterid: Optional[int] = Field(
        None, description="ID of the user who submitted the candidate"
    )
    datecreated: Optional[datetime] = Field(
        None, description="Date when the candidate was created"
    )
    tns_name: Optional[str] = Field(None, description="TNS name of the candidate")
    tns_url: Optional[str] = Field(None, description="TNS URL of the candidate")
    discovery_date: Optional[datetime] = Field(None, description="Date of discovery")
    discovery_magnitude: Optional[float] = Field(
        None, description="Magnitude at discovery"
    )
    magnitude_central_wave: Optional[float] = Field(
        None, description="Central wavelength for magnitude"
    )
    magnitude_bandwidth: Optional[float] = Field(
        None, description="Bandwidth for magnitude measurement"
    )
    magnitude_unit: Optional[str] = Field(
        None, description="Unit of magnitude measurement"
    )
    magnitude_bandpass: Optional[str] = Field(None, description="Bandpass filter used")
    associated_galaxy: Optional[str] = Field(None, description="Associated galaxy name")
    associated_galaxy_redshift: Optional[float] = Field(
        None, description="Redshift of associated galaxy"
    )
    associated_galaxy_distance: Optional[float] = Field(
        None, description="Distance to associated galaxy"
    )


# Request schema with validation
class GWCandidateCreate(GWCandidateBase):
    """Schema for creating/updating candidates with coordinate validation."""

    ra: Optional[float] = Field(
        None, ge=0.0, le=360.0, description="Right ascension in degrees (0-360)"
    )
    dec: Optional[float] = Field(
        None, ge=-90.0, le=90.0, description="Declination in degrees (-90 to +90)"
    )

    @field_validator("ra")
    @classmethod
    def validate_ra(cls, v):
        """Validate right ascension is within valid range."""
        if v is not None and (v < 0.0 or v > 360.0):
            raise ValueError("Right ascension must be between 0 and 360 degrees")
        return v

    @field_validator("dec")
    @classmethod
    def validate_dec(cls, v):
        """Validate declination is within valid range."""
        if v is not None and (v < -90.0 or v > 90.0):
            raise ValueError("Declination must be between -90 and +90 degrees")
        return v


# Response schema without strict validation (for existing data)
class GWCandidateSchema(GWCandidateBase):
    """Schema for returning candidates without strict coordinate validation."""

    id: Optional[int] = Field(None, description="Unique identifier for the candidate")
    ra: Optional[float] = Field(None, description="Right ascension in degrees")
    dec: Optional[float] = Field(None, description="Declination in degrees")

    model_config = ConfigDict(from_attributes=True)
