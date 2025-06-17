from enum import IntEnum

class PointingStatus(IntEnum):
    """Enumeration for pointing statuses."""
    planned = 1
    completed = 2
    cancelled = 3
