from enum import IntEnum

class WavelengthUnits(IntEnum):
    """Enumeration for wavelength units."""
    nanometer = 1
    angstrom = 2
    micron = 3

    @staticmethod
    def get_scale(unit):
        """Return the scale factor for the given wavelength unit."""
        if unit == WavelengthUnits.nanometer:
            return 10.0
        if unit == WavelengthUnits.angstrom:
            return 1.0
        if unit == WavelengthUnits.micron:
            return 10000.0
