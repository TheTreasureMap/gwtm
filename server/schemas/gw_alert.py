from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from server.core.enums.gw_galaxy_score_type import gw_galaxy_score_type

class GWAlertSchema(BaseModel):
    id: Optional[int] = None
    datecreated: Optional[datetime] = None
    graceid: str = Field(..., description="Grace ID of the GW event")
    alternateid: Optional[str] = None
    role: str = Field(..., description="Role of the alert (observation, test, etc.)")
    timesent: Optional[datetime] = None
    time_of_signal: Optional[datetime] = None
    packet_type: Optional[int] = None
    alert_type: str = Field(..., description="Type of alert (Initial, Update, Retraction, etc.)")
    detectors: Optional[str] = None
    description: Optional[str] = None
    far: Optional[float] = None
    skymap_fits_url: Optional[str] = None
    distance: Optional[float] = None
    distance_error: Optional[float] = None
    prob_bns: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of BNS")
    prob_nsbh: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of NSBH")
    prob_gap: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of mass gap")
    prob_bbh: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of BBH")
    prob_terrestrial: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of terrestrial")
    prob_hasns: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability has neutron star")
    prob_hasremenant: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability has remnant")
    group: Optional[str] = None
    centralfreq: Optional[float] = None
    duration: Optional[float] = None
    avgra: Optional[float] = Field(None, ge=0.0, le=360.0, description="Average right ascension")
    avgdec: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Average declination")
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

    @field_validator('far')
    @classmethod
    def validate_far(cls, v):
        """Validate False Alarm Rate is positive."""
        if v is not None and v < 0:
            raise ValueError('False Alarm Rate must be positive')
        return v

    @field_validator('distance')
    @classmethod
    def validate_distance(cls, v):
        """Validate distance is positive."""
        if v is not None and v < 0:
            raise ValueError('Distance must be positive')
        return v

    @field_validator('distance_error')
    @classmethod
    def validate_distance_error(cls, v):
        """Validate distance error is positive."""
        if v is not None and v < 0:
            raise ValueError('Distance error must be positive')
        return v

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

# Base schema with common fields
class GWCandidateBase(BaseModel):
    graceid: str
    candidate_name: str
    submitterid: Optional[int] = None
    datecreated: Optional[datetime] = None
    tns_name: Optional[str] = None
    tns_url: Optional[str] = None
    discovery_date: Optional[datetime] = None
    discovery_magnitude: Optional[float] = None
    magnitude_central_wave: Optional[float] = None
    magnitude_bandwidth: Optional[float] = None
    magnitude_unit: Optional[str] = None
    magnitude_bandpass: Optional[str] = None
    associated_galaxy: Optional[str] = None
    associated_galaxy_redshift: Optional[float] = None
    associated_galaxy_distance: Optional[float] = None

# Request schema with validation
class GWCandidateCreate(GWCandidateBase):
    """Schema for creating/updating candidates with coordinate validation."""
    ra: Optional[float] = Field(None, ge=0.0, le=360.0, description="Right ascension in degrees (0-360)")
    dec: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Declination in degrees (-90 to +90)")

    @field_validator('ra')
    @classmethod
    def validate_ra(cls, v):
        if v is not None and (v < 0.0 or v > 360.0):
            raise ValueError('Right ascension must be between 0 and 360 degrees')
        return v

    @field_validator('dec')
    @classmethod
    def validate_dec(cls, v):
        if v is not None and (v < -90.0 or v > 90.0):
            raise ValueError('Declination must be between -90 and +90 degrees')
        return v

# Response schema without strict validation (for existing data)
class GWCandidateSchema(GWCandidateBase):
    """Schema for returning candidates without strict coordinate validation."""
    id: Optional[int] = None
    ra: Optional[float] = None
    dec: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)