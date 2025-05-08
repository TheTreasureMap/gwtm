from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated

class CandidateSchema(BaseModel):
    id: int
    graceid: str
    submitterid: int
    candidate_name: str
    datecreated: Optional[datetime] = None
    tns_name: Optional[str] = None
    tns_url: Optional[str] = None
    position: Annotated[str, WKBElement] = Field(None, description="WKT representation of the position")
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
    ids: Optional[List[int]] = Field(None, description="Filter by a list of candidate IDs")
    graceid: Optional[str] = Field(None, description="Filter by Grace ID")
    userid: Optional[int] = Field(None, description="Filter by user ID")
    submitted_date_after: Optional[datetime] = Field(None, description="Filter by submission date after this timestamp")
    submitted_date_before: Optional[datetime] = Field(None, description="Filter by submission date before this timestamp")
    discovery_magnitude_gt: Optional[float] = Field(None, description="Filter by discovery magnitude greater than this value")
    discovery_magnitude_lt: Optional[float] = Field(None, description="Filter by discovery magnitude less than this value")
    discovery_date_after: Optional[datetime] = Field(None, description="Filter by discovery date after this timestamp")
    discovery_date_before: Optional[datetime] = Field(None, description="Filter by discovery date before this timestamp")
    associated_galaxy_name: Optional[str] = Field(None, description="Filter by associated galaxy name")
    associated_galaxy_redshift_gt: Optional[float] = Field(None, description="Filter by associated galaxy redshift greater than this value")
    associated_galaxy_redshift_lt: Optional[float] = Field(None, description="Filter by associated galaxy redshift less than this value")
    associated_galaxy_distance_gt: Optional[float] = Field(None, description="Filter by associated galaxy distance greater than this value")
    associated_galaxy_distance_lt: Optional[float] = Field(None, description="Filter by associated galaxy distance less than this value")
