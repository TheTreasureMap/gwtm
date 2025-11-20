from enum import IntEnum


class EnergyUnits(IntEnum):
    """Enumeration for energy units."""

    eV = 1
    keV = 2
    MeV = 3
    GeV = 4
    TeV = 5

    @staticmethod
    def get_scale(unit):
        """Return the scale factor for the given energy unit."""
        if unit == EnergyUnits.eV:
            return 1.0
        if unit == EnergyUnits.keV:
            return 1000.0
        if unit == EnergyUnits.MeV:
            return 1000000.0
        if unit == EnergyUnits.GeV:
            return 1000000000.0
        if unit == EnergyUnits.TeV:
            return 1000000000000.0
