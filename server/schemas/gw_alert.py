from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from server.core.enums.gw_galaxy_score_type import gw_galaxy_score_type

class GWAlertSchema(BaseModel):
    id: int
    datecreated: Optional[datetime] = None
    graceid: str
    alternateid: Optional[str] = None
    role: Optional[str] = None
    timesent: Optional[datetime] = None
    time_of_signal: Optional[datetime] = None
    packet_type: Optional[int] = None
    alert_type: Optional[str] = None
    detectors: Optional[str] = None
    description: Optional[str] = None
    far: Optional[float] = None
    skymap_fits_url: Optional[str] = None
    distance: Optional[float] = None
    distance_error: Optional[float] = None
    prob_bns: Optional[float] = None
    prob_nsbh: Optional[float] = None
    prob_gap: Optional[float] = None
    prob_bbh: Optional[float] = None
    prob_terrestrial: Optional[float] = None
    prob_hasns: Optional[float] = None
    prob_hasremenant: Optional[float] = None
    group: Optional[str] = None
    centralfreq: Optional[float] = None
    duration: Optional[float] = None
    avgra: Optional[float] = None
    avgdec: Optional[float] = None
    observing_run: Optional[str] = None
    pipeline: Optional[str] = None
    search: Optional[str] = None
    area_50: Optional[float] = None
    area_90: Optional[float] = None
    gcn_notice_id: Optional[int] = None
    ivorn: Optional[str] = None
    ext_coinc_observatory: Optional[str] = None
    ext_coinc_search: Optional[str] = None
    time_coincidence_far: Optional[float] = None
    time_sky_position_coincidence_far: Optional[float] = None
    time_difference: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class GWGalaxySchema(BaseModel):
    id: int
    graceid: str
    galaxy_catalog: Optional[int] = None
    galaxy_catalogID: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class EventGalaxySchema(BaseModel):
    id: int
    graceid: str
    galaxy_catalog: Optional[int] = None
    galaxy_catalogID: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class GWGalaxyScoreSchema(BaseModel):
    id: int
    gw_galaxyID: int
    score_type: Optional[gw_galaxy_score_type] = None
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class GWCandidateSchema(BaseModel):
    id: Optional[int] = None
    name: str
    ra: float
    dec: float
    error_radius: float
    user_id: Optional[int] = None
    datecreated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
