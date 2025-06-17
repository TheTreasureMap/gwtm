from sqlalchemy import Column, Integer, String
from ..database import Base

class PointingEvent(Base):
    __tablename__ = 'pointing_event'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True)
    pointingid = Column(Integer, index=True)
    graceid = Column(String, index=True)
