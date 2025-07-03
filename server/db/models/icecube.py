from sqlalchemy import Column, Integer, String, DateTime, Float
from ..database import Base


class IceCubeNotice(Base):
    __tablename__ = "icecube_notice"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    ref_id = Column(String)
    graceid = Column(String)
    alert_datetime = Column(DateTime)
    datecreated = Column(DateTime)
    observation_start = Column(DateTime)
    observation_stop = Column(DateTime)
    pval_generic = Column(Float)
    pval_bayesian = Column(Float)
    most_probable_direction_ra = Column(Float)
    most_probable_direction_dec = Column(Float)
    flux_sens_low = Column(Float)
    flux_sens_high = Column(Float)
    sens_energy_range_low = Column(Float)
    sens_energy_range_high = Column(Float)


class IceCubeNoticeCoincEvent(Base):
    __tablename__ = "icecube_notice_coinc_event"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    icecube_notice_id = Column(Integer)
    datecreated = Column(DateTime)
    event_dt = Column(Float)
    ra = Column(Float)
    dec = Column(Float)
    containment_probability = Column(Float)
    event_pval_generic = Column(Float)
    event_pval_bayesian = Column(Float)
    ra_uncertainty = Column(Float)
    uncertainty_shape = Column(String)
