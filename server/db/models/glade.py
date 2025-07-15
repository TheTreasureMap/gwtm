# `server/db/models/glade.py`
from sqlalchemy import Column, Integer, Float, String
from geoalchemy2 import Geography
from ..database import Base


class Glade2P3(Base):
    __tablename__ = "glade_2p3"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    pgc_number = Column(Integer)
    distance = Column(Float)
    distance_error = Column(Float)
    redshift = Column(Float)
    bmag = Column(Float)
    bmag_err = Column(Float)
    position = Column(Geography("POINT", srid=4326))
    _2mass_name = Column(String)
    gwgc_name = Column(String)
    hyperleda_name = Column(String)
    sdssdr12_name = Column(String)
