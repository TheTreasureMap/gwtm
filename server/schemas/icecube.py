from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class IceCubeNoticeSchema(BaseModel):
    id: int
    ref_id: str
    graceid: str
    alert_datetime: Optional[datetime] = None
    datecreated: Optional[datetime] = None
    observation_start: Optional[datetime] = None
    observation_stop: Optional[datetime] = None
    pval_generic: Optional[float] = None
    pval_bayesian: Optional[float] = None
    most_probable_direction_ra: Optional[float] = None
    most_probable_direction_dec: Optional[float] = None
    flux_sens_low: Optional[float] = None
    flux_sens_high: Optional[float] = None
    sens_energy_range_low: Optional[float] = None
    sens_energy_range_high: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class IceCubeNoticeCoincEventSchema(BaseModel):
    id: int
    icecube_notice_id: int
    datecreated: Optional[datetime] = None
    event_dt: Optional[float] = None
    ra: Optional[float] = None
    dec: Optional[float] = None
    containment_probability: Optional[float] = None
    event_pval_generic: Optional[float] = None
    event_pval_bayesian: Optional[float] = None
    ra_uncertainty: Optional[float] = None
    uncertainty_shape: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)