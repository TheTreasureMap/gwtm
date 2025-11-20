from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class IceCubeNoticeCreateSchema(BaseModel):
    """Schema for creating a new IceCube notice."""

    ref_id: str = Field(..., description="Reference ID for the IceCube notice")
    graceid: str = Field(..., description="Grace ID of the associated GW event")
    alert_datetime: Optional[datetime] = Field(
        None, description="Date and time of the alert"
    )
    observation_start: Optional[datetime] = Field(
        None, description="Start time of the observation period"
    )
    observation_stop: Optional[datetime] = Field(
        None, description="End time of the observation period"
    )
    pval_generic: Optional[float] = Field(
        None, description="Generic p-value for the event"
    )
    pval_bayesian: Optional[float] = Field(
        None, description="Bayesian p-value for the event"
    )
    most_probable_direction_ra: Optional[float] = Field(
        None, description="Right ascension of most probable direction"
    )
    most_probable_direction_dec: Optional[float] = Field(
        None, description="Declination of most probable direction"
    )
    flux_sens_low: Optional[float] = Field(
        None, description="Lower bound of flux sensitivity"
    )
    flux_sens_high: Optional[float] = Field(
        None, description="Upper bound of flux sensitivity"
    )
    sens_energy_range_low: Optional[float] = Field(
        None, description="Lower bound of sensitivity energy range"
    )
    sens_energy_range_high: Optional[float] = Field(
        None, description="Upper bound of sensitivity energy range"
    )


class IceCubeNoticeCoincEventCreateSchema(BaseModel):
    """Schema for creating a new IceCube notice coincident event."""

    event_dt: Optional[float] = Field(None, description="Event time difference")
    ra: Optional[float] = Field(None, description="Right ascension of the event")
    dec: Optional[float] = Field(None, description="Declination of the event")
    containment_probability: Optional[float] = Field(
        None, description="Probability of event containment"
    )
    event_pval_generic: Optional[float] = Field(
        None, description="Generic p-value for this specific event"
    )
    event_pval_bayesian: Optional[float] = Field(
        None, description="Bayesian p-value for this specific event"
    )
    ra_uncertainty: Optional[float] = Field(
        None, description="Uncertainty in right ascension"
    )
    uncertainty_shape: Optional[str] = Field(
        None, description="Shape of the uncertainty region"
    )


class IceCubeNoticeRequestSchema(BaseModel):
    """Schema for submitting an IceCube notice with associated events."""

    notice_data: IceCubeNoticeCreateSchema = Field(..., description="Main notice data")
    events_data: List[IceCubeNoticeCoincEventCreateSchema] = Field(
        ..., description="List of coincident events"
    )


class IceCubeNoticeSchema(BaseModel):
    """Schema for returning an IceCube notice."""

    id: int = Field(..., description="Unique identifier for the notice")
    ref_id: str = Field(..., description="Reference ID for the IceCube notice")
    graceid: str = Field(..., description="Grace ID of the associated GW event")
    alert_datetime: Optional[datetime] = Field(
        None, description="Date and time of the alert"
    )
    datecreated: Optional[datetime] = Field(
        None, description="Date when the notice was created"
    )
    observation_start: Optional[datetime] = Field(
        None, description="Start time of the observation period"
    )
    observation_stop: Optional[datetime] = Field(
        None, description="End time of the observation period"
    )
    pval_generic: Optional[float] = Field(
        None, description="Generic p-value for the event"
    )
    pval_bayesian: Optional[float] = Field(
        None, description="Bayesian p-value for the event"
    )
    most_probable_direction_ra: Optional[float] = Field(
        None, description="Right ascension of most probable direction"
    )
    most_probable_direction_dec: Optional[float] = Field(
        None, description="Declination of most probable direction"
    )
    flux_sens_low: Optional[float] = Field(
        None, description="Lower bound of flux sensitivity"
    )
    flux_sens_high: Optional[float] = Field(
        None, description="Upper bound of flux sensitivity"
    )
    sens_energy_range_low: Optional[float] = Field(
        None, description="Lower bound of sensitivity energy range"
    )
    sens_energy_range_high: Optional[float] = Field(
        None, description="Upper bound of sensitivity energy range"
    )

    model_config = ConfigDict(from_attributes=True)


class IceCubeNoticeCoincEventSchema(BaseModel):
    """Schema for returning an IceCube notice coincident event."""

    id: int = Field(..., description="Unique identifier for the event")
    icecube_notice_id: int = Field(
        ..., description="ID of the associated IceCube notice"
    )
    datecreated: Optional[datetime] = Field(
        None, description="Date when the event was created"
    )
    event_dt: Optional[float] = Field(None, description="Event time difference")
    ra: Optional[float] = Field(None, description="Right ascension of the event")
    dec: Optional[float] = Field(None, description="Declination of the event")
    containment_probability: Optional[float] = Field(
        None, description="Probability of event containment"
    )
    event_pval_generic: Optional[float] = Field(
        None, description="Generic p-value for this specific event"
    )
    event_pval_bayesian: Optional[float] = Field(
        None, description="Bayesian p-value for this specific event"
    )
    ra_uncertainty: Optional[float] = Field(
        None, description="Uncertainty in right ascension"
    )
    uncertainty_shape: Optional[str] = Field(
        None, description="Shape of the uncertainty region"
    )

    model_config = ConfigDict(from_attributes=True)
