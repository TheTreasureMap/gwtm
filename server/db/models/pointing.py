from sqlalchemy import Column, Integer, Float, DateTime, Enum, String
from geoalchemy2 import Geography
from ..database import Base
from server.core.enums.bandpass import bandpass
from server.core.enums.depth_unit import depth_unit
from server.core.enums.pointing_status import pointing_status

class Pointing(Base):
    __tablename__ = 'pointing'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    status = Column(Enum(pointing_status))
    position = Column(Geography('POINT', srid=4326))
    galaxy_catalog = Column(Integer)
    galaxy_catalogid = Column(Integer)
    instrumentid = Column(Integer)
    depth = Column(Float)
    depth_err = Column(Float)
    depth_unit = Column(Enum(depth_unit))
    time = Column(DateTime)
    datecreated = Column(DateTime)
    dateupdated = Column(DateTime)
    submitterid = Column(Integer)
    pos_angle = Column(Float)
    band = Column(Enum(bandpass))
    doi_url = Column(String(100))
    doi_id = Column(Integer)
    central_wave = Column(Float)
    bandwidth = Column(Float)
