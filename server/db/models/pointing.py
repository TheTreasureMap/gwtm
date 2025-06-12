from sqlalchemy import Column, Integer, Float, DateTime, Enum, String, and_
from sqlalchemy.ext.hybrid import hybrid_method
from geoalchemy2 import Geography
from ..database import Base
from server.core.enums.bandpass import bandpass
from server.core.enums.depth_unit import depth_unit
from server.core.enums.pointing_status import pointing_status
from server.utils.spectral import SpectralRangeHandler


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

    @hybrid_method
    def inSpectralRange(self, spectral_min, spectral_max, spectral_type):
        """
        Function to determine if a pointing is within a given range for spectral types:
            wavelength (Angstroms)
            energy (eV)
            frequency (Hz)

        It inputs the range of the spectral type (minimum and maximum values for given type) and
        determines if the pointing's observation is in that range. The boolean logic is all
        encompassing; whether the endpoints are confined entirely within the provided range
        """
        if spectral_type == SpectralRangeHandler.spectralrangetype.wavelength:
            thismin, thismax = SpectralRangeHandler.wavetoWaveRange(self.central_wave, self.bandwidth)
        elif spectral_type == SpectralRangeHandler.spectralrangetype.energy:
            thismin, thismax = SpectralRangeHandler.wavetoEnergy(self.central_wave, self.bandwidth)
        elif spectral_type == SpectralRangeHandler.spectralrangetype.frequency:
            thismin, thismax = SpectralRangeHandler.wavetoFrequency(self.central_wave, self.bandwidth)
        else:
            return False

        if thismin >= spectral_min and thismax <= spectral_max:
            return True

        return False

    @inSpectralRange.expression
    def inSpectralRange(cls, spectral_min, spectral_max, spectral_type):
        """
        SQLAlchemy expression version of inSpectralRange for database queries
        """
        if spectral_type == SpectralRangeHandler.spectralrangetype.wavelength:
            thismin, thismax = SpectralRangeHandler.wavetoWaveRange(cls.central_wave, cls.bandwidth)
        elif spectral_type == SpectralRangeHandler.spectralrangetype.energy:
            thismin, thismax = SpectralRangeHandler.wavetoEnergy(cls.central_wave, cls.bandwidth)
        elif spectral_type == SpectralRangeHandler.spectralrangetype.frequency:
            thismin, thismax = SpectralRangeHandler.wavetoFrequency(cls.central_wave, cls.bandwidth)
        else:
            return False

        return and_(thismin >= spectral_min, thismax <= spectral_max)
