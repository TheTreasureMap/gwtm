from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from geoalchemy2 import Geography
import shapely.wkb
from sqlalchemy.ext.hybrid import hybrid_property
from ..database import Base
from server.core.enums.instrumenttype import InstrumentType
import datetime


class Instrument(Base):
    __tablename__ = "instrument"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    instrument_name = Column(String(64))
    nickname = Column(String(25))
    instrument_type = Column(Enum(InstrumentType, name="instrumenttype"))
    datecreated = Column(DateTime)
    submitterid = Column(Integer)


class FootprintCCD(Base):
    __tablename__ = "footprint_ccd"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    instrumentid = Column(Integer)
    footprint = Column(Geography("POLYGON", srid=4326))
