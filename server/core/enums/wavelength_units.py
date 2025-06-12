from enum import IntEnum

class wavelength_units(IntEnum):
    """Enumeration for wavelength units."""
    nanometer = 1
    angstrom = 2
    micron = 3

    @staticmethod
    def get_scale(unit):
        """Return the scale factor for the given wavelength unit."""
        if unit == wavelength_units.nanometer:
            return 10.0
        if unit == wavelength_units.angstrom:
            return 1.0
        if unit == wavelength_units.micron:
            return 10000.0