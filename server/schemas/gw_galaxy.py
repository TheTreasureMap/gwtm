from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from dateutil.parser import parse as date_parse
from server.core.enums.gwgalaxyscoretype import GwGalaxyScoreType


class GWGalaxySchema(BaseModel):
    """Pydantic schema for GWGalaxy model."""
    id: Optional[int] = None
    graceid: str
    galaxy_catalog: Optional[int] = None
    galaxy_catalogid: Optional[int] = None
    reference: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventGalaxySchema(BaseModel):
    """Pydantic schema for EventGalaxy model."""
    id: Optional[int] = None
    graceid: str
    galaxy_catalog: Optional[int] = None
    galaxy_catalogid: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GWGalaxyScoreSchema(BaseModel):
    """Pydantic schema for GWGalaxyScore model."""
    id: Optional[int] = None
    gw_galaxyid: int
    score_type: Optional[GwGalaxyScoreType] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class GWGalaxyListSchema(BaseModel):
    """Pydantic schema for GWGalaxyList model."""
    id: Optional[int] = None
    graceid: str
    groupname: str
    submitterid: Optional[int] = None
    reference: Optional[str] = None
    alertid: Optional[str] = None
    doi_url: Optional[str] = None
    doi_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class GWGalaxyEntrySchema(BaseModel):
    """Pydantic schema for GWGalaxyEntry model."""
    id: Optional[int] = None
    listid: int
    name: str
    score: float
    position: Optional[str] = None
    rank: int
    info: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class GalaxyPosition(BaseModel):
    """Schema for position data using RA and Dec."""
    ra: float = Field(..., description="Right ascension in degrees")
    dec: float = Field(..., description="Declination in degrees")


class GalaxyEntryCreate(BaseModel):
    """Schema for creating a new GWGalaxyEntry."""
    name: str = Field(..., description="Name of the galaxy")
    score: float = Field(..., description="Score or probability value for this galaxy")
    position: Optional[str] = Field(None, description="WKT representation of position (e.g., 'POINT(10.5 -20.3)')")
    ra: Optional[float] = Field(None, description="Right ascension in degrees")
    dec: Optional[float] = Field(None, description="Declination in degrees")
    rank: int = Field(..., description="Rank of this galaxy in the list")
    info: Optional[Dict[str, Any]] = Field(None, description="Additional information about the galaxy")

    @model_validator(mode='after')
    def check_position_data(self) -> 'GalaxyEntryCreate':
        """Validate that either position or ra/dec are provided."""
        position = self.position
        ra = self.ra
        dec = self.dec

        # If position string is provided, validate it's in correct format
        if position is not None:
            if not all(x in position for x in ["POINT", "(", ")", " "]) or "," in position:
                raise ValueError("Position must be in WKT format: 'POINT(lon lat)'")
            return self

        # If no position string, ra and dec must both be provided
        if ra is None or dec is None:
            raise ValueError("Either position string or both ra and dec must be provided")

        return self


class DOICreator(BaseModel):
    """Schema for a DOI creator/author."""
    name: str = Field(..., description="Author name")
    affiliation: str = Field(..., description="Author affiliation")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    gnd: Optional[str] = Field(None, description="GND identifier")


class PostEventGalaxiesRequest(BaseModel):
    """Schema for posting galaxy entries for a GW event."""
    graceid: str = Field(..., description="Grace ID of the GW event")
    timesent_stamp: str = Field(..., description="Timestamp of the event in ISO format")
    groupname: Optional[str] = Field(None, description="Group name for the galaxy list")
    reference: Optional[str] = Field(None, description="Reference for the galaxy list")
    request_doi: Optional[bool] = Field(False, description="Whether to request a DOI")
    creators: Optional[List[DOICreator]] = Field(
        None, description="List of creators with name and affiliation"
    )
    doi_group_id: Optional[Union[int, str]] = Field(None, description="ID or name of the DOI group")
    galaxies: List[GalaxyEntryCreate] = Field(..., description="List of galaxy entries")

    @field_validator('timesent_stamp')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate that the timestamp is in a valid ISO format."""
        try:
            date_parse(v)
            return v
        except Exception:
            raise ValueError("Time format must be %Y-%m-%dT%H:%M:%S.%f, e.g. 2019-05-01T12:00:00.00")


class PostEventGalaxiesResponse(BaseModel):
    """Schema for the response when posting galaxy entries."""
    message: str = Field(..., description="Success message")
    errors: List[Any] = Field(..., description="List of errors encountered")
    warnings: List[Any] = Field(..., description="List of warnings encountered")
