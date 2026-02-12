"""Type checking and conversion utilities."""


def is_int(s) -> bool:
    """Check if a value can be converted to an integer."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def is_float(s) -> bool:
    """Check if a value can be converted to a float."""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def float_or_none(i):
    """Convert a value to float, returning None if the input is None or unconvertible."""
    if i is None:
        return None
    try:
        return float(i)
    except (ValueError, TypeError):
        return None
