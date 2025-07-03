from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from server.core.enums.depthunit import DepthUnit as depth_unit_enum
from geoalchemy2 import Geography
from sqlalchemy.ext.hybrid import hybrid_property
from ..database import Base
import shapely.wkb
from datetime import datetime
from typing import Dict, Any, Optional, List


class ValidationResult:
    """Helper class for validation results"""

    def __init__(self):
        self.valid = True
        self.errors = []
        self.warnings = []


class GWCandidate(Base):
    __tablename__ = "gw_candidate"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    graceid = Column(String(50), nullable=False)
    submitterid = Column(Integer, nullable=False)
    candidate_name = Column(String(100), nullable=False)
    datecreated = Column(DateTime, default=datetime.now)
    tns_name = Column(String(100))
    tns_url = Column(String(500))
    position = Column(Geography("POINT", srid=4326), nullable=False)
    discovery_date = Column(DateTime)
    discovery_magnitude = Column(Float)
    magnitude_central_wave = Column(Float)
    magnitude_bandwidth = Column(Float)
    magnitude_unit = Column(Enum(depth_unit_enum, name="depthunit"), nullable=False)
    magnitude_bandpass = Column(String(50))
    associated_galaxy = Column(String(100))
    associated_galaxy_redshift = Column(Float)
    associated_galaxy_distance = Column(Float)

    @hybrid_property
    def ra(self) -> Optional[float]:
        """Get RA coordinate from position"""
        try:
            position_geom = shapely.wkb.loads(bytes(self.position.data))
            coords = str(position_geom).replace("POINT (", "").replace(")", "").split()
            return float(coords[0])
        except (AttributeError, Exception):
            return None

    @hybrid_property
    def dec(self) -> Optional[float]:
        """Get Dec coordinate from position"""
        try:
            position_geom = shapely.wkb.loads(bytes(self.position.data))
            coords = str(position_geom).replace("POINT (", "").replace(")", "").split()
            return float(coords[1])
        except (AttributeError, Exception):
            return None

    @hybrid_property
    def position_wkt(self) -> Optional[str]:
        """Get position as WKT string"""
        try:
            position_geom = shapely.wkb.loads(bytes(self.position.data))
            return str(position_geom)
        except (AttributeError, Exception):
            return None
