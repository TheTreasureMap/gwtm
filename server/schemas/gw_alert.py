from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime


class GWAlertSchema(BaseModel):
    id: Optional[int] = None
    datecreated: Optional[datetime] = None
    graceid: str = Field(..., description="Grace ID of the GW event")
    alternateid: Optional[str] = None
    role: str = Field(..., description="Role of the alert (observation, test, etc.)")
    timesent: Optional[datetime] = None
    time_of_signal: Optional[datetime] = None
    packet_type: Optional[int] = None
    alert_type: str = Field(
        ..., description="Type of alert (Initial, Update, Retraction, etc.)"
    )
    detectors: Optional[str] = None
    description: Optional[str] = None
    far: Optional[float] = None
    skymap_fits_url: Optional[str] = None
    distance: Optional[float] = None
    distance_error: Optional[float] = None
    prob_bns: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability of BNS"
    )
    prob_nsbh: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability of NSBH"
    )
    prob_gap: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability of mass gap"
    )
    prob_bbh: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability of BBH"
    )
    prob_terrestrial: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability of terrestrial"
    )
    prob_hasns: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability has neutron star"
    )
    prob_hasremenant: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Probability has remnant"
    )
    group: Optional[str] = None
    centralfreq: Optional[float] = None
    duration: Optional[float] = None
    avgra: Optional[float] = Field(
        None, ge=0.0, le=360.0, description="Average right ascension"
    )
    avgdec: Optional[float] = Field(
        None, ge=-90.0, le=90.0, description="Average declination"
    )
    observing_run: Optional[str] = None
    pipeline: Optional[str] = None
    search: Optional[str] = None
    area_50: Optional[float] = Field(None, ge=0.0, description="50% confidence area")
    area_90: Optional[float] = Field(None, ge=0.0, description="90% confidence area")
    gcn_notice_id: Optional[int] = None
    ivorn: Optional[str] = None
    ext_coinc_observatory: Optional[str] = None
    ext_coinc_search: Optional[str] = None
    time_coincidence_far: Optional[float] = None
    time_sky_position_coincidence_far: Optional[float] = None
    time_difference: Optional[float] = None

    @field_validator("far")
    @classmethod
    def validate_far(cls, v):
        """Validate False Alarm Rate is positive."""
        if v is not None and v < 0:
            raise ValueError("False Alarm Rate must be positive")
        return v

    @field_validator("distance")
    @classmethod
    def validate_distance(cls, v):
        """Validate distance is positive."""
        if v is not None and v < 0:
            raise ValueError("Distance must be positive")
        return v

    @field_validator("distance_error")
    @classmethod
    def validate_distance_error(cls, v):
        """Validate distance error is positive."""
        if v is not None and v < 0:
            raise ValueError("Distance error must be positive")
        return v

    model_config = ConfigDict(from_attributes=True)
