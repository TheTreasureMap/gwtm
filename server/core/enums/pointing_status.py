from enum import IntEnum

class pointing_status(IntEnum):
    """Enumeration for pointing statuses."""
    planned = 1
    completed = 2
    cancelled = 3