from enum import IntEnum


class FrequencyUnits(IntEnum):
    """Enumeration for frequency units."""

    Hz = 1
    kHz = 2
    GHz = 3
    MHz = 4
    THz = 5

    @staticmethod
    def get_scale(unit):
        """Return the scale factor for the given frequency unit."""
        if unit == FrequencyUnits.Hz:
            return 1.0
        if unit == FrequencyUnits.kHz:
            return 1e3
        if unit == FrequencyUnits.MHz:
            return 1e6
        if unit == FrequencyUnits.GHz:
            return 1e9
        if unit == FrequencyUnits.THz:
            return 1e12
