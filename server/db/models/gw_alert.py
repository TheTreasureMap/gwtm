from sqlalchemy import Column, Integer, Float, String, DateTime
from ..database import Base
from datetime import datetime


class GWAlert(Base):
    __tablename__ = "gw_alert"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    datecreated = Column(DateTime, default=datetime.now)
    graceid = Column(String(50), nullable=False, index=True)
    alternateid = Column(String(50), index=True)
    role = Column(String(20), default="observation", index=True)  # observation or test
    timesent = Column(DateTime)
    time_of_signal = Column(DateTime, index=True)
    packet_type = Column(Integer)
    alert_type = Column(String(50))
    detectors = Column(String(100))
    description = Column(String(500))
    far = Column(Float, default=0, index=True)
    skymap_fits_url = Column(String(500))
    distance = Column(Float)
    distance_error = Column(Float)
    prob_bns = Column(Float)
    prob_nsbh = Column(Float)
    prob_gap = Column(Float)
    prob_bbh = Column(Float)
    prob_terrestrial = Column(Float)
    prob_hasns = Column(Float)
    prob_hasremenant = Column(Float)
    group = Column(String(50))
    centralfreq = Column(Float)
    duration = Column(Float)
    avgra = Column(Float)
    avgdec = Column(Float, index=True)
    observing_run = Column(String(20))
    pipeline = Column(String(50))
    search = Column(String(50))
    area_50 = Column(Float)
    area_90 = Column(Float)
    gcn_notice_id = Column(Integer)
    ivorn = Column(String(100))
    ext_coinc_observatory = Column(String(50))
    ext_coinc_search = Column(String(50))
    time_difference = Column(Float)
    time_coincidence_far = Column(Float)
    time_sky_position_coincidence_far = Column(Float)

    def getClassification(self) -> str:
        """Get classification based on probabilities."""
        if self.group == "Burst":
            return "None (detected as burst)"

        probs = [
            {"prob": self.prob_bns if self.prob_bns else 0.0, "class": "BNS"},
            {"prob": self.prob_nsbh if self.prob_nsbh else 0.0, "class": "NSBH"},
            {"prob": self.prob_bbh if self.prob_bbh else 0.0, "class": "BBH"},
            {
                "prob": self.prob_terrestrial if self.prob_terrestrial else 0.0,
                "class": "Terrestrial",
            },
            {"prob": self.prob_gap if self.prob_gap else 0.0, "class": "Mass Gap"},
        ]

        sorted_probs = sorted(
            [x for x in probs if x["prob"] > 0.01],
            key=lambda i: i["prob"],
            reverse=True,
        )

        classification = ""
        for p in sorted_probs:
            classification += (
                p["class"] + ": (" + str(round(100 * p["prob"], 1)) + "%) "
            )

        return classification

    @staticmethod
    def graceidfromalternate(graceid: str, db=None) -> str:
        """
        Look up the canonical graceid for a given alternate ID.

        If the input matches an alternateid in the database, returns the
        corresponding graceid. Otherwise returns the input unchanged.

        Args:
            graceid: The GraceID or alternate ID to normalize
            db: SQLAlchemy Session (required for DB lookup)

        Returns:
            Canonical GraceID
        """
        if db is not None:
            match = db.query(GWAlert).filter(GWAlert.alternateid == graceid).first()
            if match:
                return match.graceid
        return graceid

    @staticmethod
    def alternatefromgraceid(graceid: str, db=None) -> str:
        """
        Look up the alternate ID for a given canonical graceid.

        If the graceid has a non-empty alternateid in the database, returns it.
        Otherwise returns the input unchanged.

        Args:
            graceid: The canonical GraceID
            db: SQLAlchemy Session (required for DB lookup)

        Returns:
            Alternate ID if found, otherwise the original graceid
        """
        if db is not None:
            match = (
                db.query(GWAlert)
                .filter(
                    GWAlert.graceid == graceid,
                    GWAlert.alternateid != "",
                    GWAlert.alternateid.isnot(None),
                )
                .first()
            )
            if match:
                return match.alternateid
        return graceid
