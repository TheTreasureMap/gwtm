from enum import IntEnum

class energy_units(IntEnum):
    """Enumeration for energy units."""
    eV = 1
    keV = 2
    MeV = 3
    GeV = 4
    TeV = 5

    @staticmethod
    def get_scale(unit):
        """Return the scale factor for the given energy unit."""
        if unit == energy_units.eV:
            return 1.0
        if unit == energy_units.keV:
            return 1000.0
        if unit == energy_units.MeV:
            return 1000000.0
        if unit == energy_units.GeV:
            return 1000000000.0
        if unit == energy_units.TeV:
            return 1000000000000.0