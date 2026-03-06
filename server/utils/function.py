"""Utility functions — re-exported from focused modules.

This module exists for backward compatibility. New code should import
directly from the specific modules:

    from server.utils.type_checks import is_int, is_float, float_or_none
    from server.utils.geometry import sanatize_pointing, project_footprint, ...
    from server.utils.doi import create_doi, create_pointing_doi, ...
    from server.utils.formatters import get_farrate_farunit, by_chunk, ...
"""

# Type checks (snake_case canonical names)
from server.utils.type_checks import is_int, is_float, float_or_none

# Backward-compatible camelCase aliases
isInt = is_int
isFloat = is_float
floatNone = float_or_none

# Geometry / coordinates
from server.utils.geometry import (  # noqa: E402
    sanatize_pointing,
    sanatize_footprint_ccds,
    ra_dec_to_uvec,
    uvec_to_ra_dec,
    x_rot,
    y_rot,
    z_rot,
    project_footprint,
    polygons2footprints,
    pointing_crossmatch,
)

# DOI creation
from server.utils.doi import (  # noqa: E402
    create_doi,
    create_pointing_doi,
    create_galaxy_score_doi,
)

# Formatters
from server.utils.formatters import (  # noqa: E402
    get_farrate_farunit,
    sanatize_gal_info,
    sanatize_icecube_event,
    sanatize_candidate_info,
    sanatize_XRT_source_info,
    by_chunk,
)
