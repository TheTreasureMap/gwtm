from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Enum
from geoalchemy2 import Geography
from ..database import Base
import datetime
from server.core.enums.gwgalaxyscoretype import GwGalaxyScoreType


class GWGalaxy(Base):
    """
    Gravitational Wave Galaxy mapping.
    Maps gravitational wave events to specific galaxies from catalogs.
    """

    __tablename__ = "gw_galaxy"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    graceid = Column(String)
    galaxy_catalog = Column(Integer)
    galaxy_catalogid = Column(Integer)
    reference = Column(String)


class EventGalaxy(Base):
    """
    Event to Galaxy mapping.
    Maps event IDs to galaxies in catalogs.
    """

    __tablename__ = "event_galaxy"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    graceid = Column(String)
    galaxy_catalog = Column(Integer)
    galaxy_catalogid = Column(Integer)


class GWGalaxyScore(Base):
    """
    Gravitational Wave Galaxy Score.
    Stores scores for galaxies associated with GW events.
    """

    __tablename__ = "gw_galaxy_score"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    gw_galaxyid = Column(Integer)
    score_type = Column(Enum(GwGalaxyScoreType, name="gwgalaxyscoretype"))
    score = Column(Float)


class GWGalaxyList(Base):
    """
    Gravitational Wave Galaxy List.
    Represents a list of galaxies associated with a GW event.
    """

    __tablename__ = "gw_galaxy_list"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    graceid = Column(String)
    groupname = Column(String)
    submitterid = Column(Integer)
    reference = Column(String)
    alertid = Column(String)
    doi_url = Column(String(100))
    doi_id = Column(Integer)


class GWGalaxyEntry(Base):
    """
    Gravitational Wave Galaxy Entry.
    Individual galaxy entries within a galaxy list.
    """

    __tablename__ = "gw_galaxy_entry"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    listid = Column(Integer)
    name = Column(String)
    score = Column(Float)
    position = Column(Geography("POINT", srid=4326))
    rank = Column(Integer)
    info = Column(JSON)
