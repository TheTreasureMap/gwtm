from enum import IntEnum


class DepthUnit(IntEnum):
    """Enumeration for depth units."""

    ab_mag = 1
    vega_mag = 2
    flux_erg = 3
    flux_jy = 4

    def __str__(self) -> str:
        """Return a formatted string representation of the depth unit."""
        split_name = str(self.name).split("_")
        return str.upper(split_name[0]) + " " + split_name[1]
