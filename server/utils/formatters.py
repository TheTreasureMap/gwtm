"""Data formatting utilities for display."""

import json
from typing import List, Dict, Any, Tuple


def get_farrate_farunit(far: float) -> Tuple[float, str]:
    """
    Convert FAR (False Alarm Rate) to human readable format.

    Args:
        far: False Alarm Rate in Hz

    Returns:
        Tuple of (rate, unit) where unit is a time unit (years, days, hours, etc.)
    """
    far_rate_dict = {
        "second": 1 / far,
        "minute": 1 / far / 60,
        "hour": 1 / far / 3600,
        "day": 1 / far / 3600 / 24,
        "month": 1 / far / 3600 / 24 / 30,
        "year": 1 / far / 3600 / 24 / 365,
        "decade": 1 / far / 3600 / 24 / 365 / 10,
        "century": 1 / far / 3600 / 24 / 365 / 100,
        "millennium": 1 / far / 3600 / 24 / 365 / 1000,
    }

    if far_rate_dict["second"] < 60:
        return far_rate_dict["second"], "seconds"
    if far_rate_dict["minute"] < 60:
        return far_rate_dict["minute"], "minutes"
    if far_rate_dict["hour"] < 24:
        return far_rate_dict["hour"], "hours"
    if far_rate_dict["day"] < 30:
        return far_rate_dict["day"], "days"
    if far_rate_dict["month"] < 12:
        return far_rate_dict["month"], "months"
    if far_rate_dict["year"] < 10:
        return far_rate_dict["year"], "years"
    if far_rate_dict["decade"] < 10:
        return far_rate_dict["decade"], "decades"
    if far_rate_dict["century"] < 10:
        return far_rate_dict["century"], "centuries"

    return far_rate_dict["millennium"], "millennia"


def sanatize_gal_info(galaxy_entry, galaxy_list) -> Dict[str, Any]:
    """
    Format galaxy information for display.

    Args:
        galaxy_entry: A galaxy entry object
        galaxy_list: The parent galaxy list object

    Returns:
        Formatted galaxy information as a dictionary
    """
    info_dict = {}

    if hasattr(galaxy_entry, "info") and galaxy_entry.info:
        # Check if info is already a dict (SQLAlchemy JSON column) or a string
        if isinstance(galaxy_entry.info, dict):
            info_dict = galaxy_entry.info.copy()
        elif isinstance(galaxy_entry.info, str):
            try:
                info_dict = json.loads(galaxy_entry.info)
            except json.JSONDecodeError:
                info_dict = {}
        else:
            # Handle other types by converting to empty dict
            info_dict = {}

    # Add galaxy list information
    info_dict["Group"] = (
        galaxy_list.groupname if hasattr(galaxy_list, "groupname") else ""
    )
    info_dict["Score"] = galaxy_entry.score if hasattr(galaxy_entry, "score") else ""
    info_dict["Rank"] = galaxy_entry.rank if hasattr(galaxy_entry, "rank") else ""

    return info_dict


def sanatize_icecube_event(event, notice) -> Dict[str, Any]:
    """
    Format IceCube event information for display.

    Args:
        event: An IceCube event object
        notice: The parent IceCube notice object

    Returns:
        Formatted IceCube event information as a dictionary
    """
    info_dict = {
        "Event ID": event.id if hasattr(event, "id") else "",
        "Notice ID": notice.id if hasattr(notice, "id") else "",
        "RA": event.ra if hasattr(event, "ra") else "",
        "Dec": event.dec if hasattr(event, "dec") else "",
        "Uncertainty": event.ra_uncertainty if hasattr(event, "ra_uncertainty") else "",
        "Event p-value (generic)": (
            event.event_pval_generic if hasattr(event, "event_pval_generic") else ""
        ),
        "Event p-value (Bayesian)": (
            event.event_pval_bayesian if hasattr(event, "event_pval_bayesian") else ""
        ),
        "Event DT": event.event_dt if hasattr(event, "event_dt") else "",
    }

    return info_dict


def sanatize_candidate_info(candidate, ra, dec) -> Dict[str, Any]:
    """
    Format candidate information for display.

    Args:
        candidate: A candidate object
        ra: Right ascension
        dec: Declination

    Returns:
        Formatted candidate information as a dictionary
    """
    info_dict = {
        "Candidate Name": (
            candidate.candidate_name if hasattr(candidate, "candidate_name") else ""
        ),
        "TNS Name": candidate.tns_name if hasattr(candidate, "tns_name") else "",
        "TNS URL": candidate.tns_url if hasattr(candidate, "tns_url") else "",
        "RA": ra,
        "Dec": dec,
        "Discovery Date": (
            candidate.discovery_date.isoformat()
            if hasattr(candidate, "discovery_date") and candidate.discovery_date
            else ""
        ),
        "Discovery Magnitude": (
            candidate.discovery_magnitude
            if hasattr(candidate, "discovery_magnitude")
            else ""
        ),
        "Associated Galaxy": (
            candidate.associated_galaxy
            if hasattr(candidate, "associated_galaxy")
            else ""
        ),
        "Associated Galaxy Redshift": (
            candidate.associated_galaxy_redshift
            if hasattr(candidate, "associated_galaxy_redshift")
            else ""
        ),
        "Associated Galaxy Distance": (
            candidate.associated_galaxy_distance
            if hasattr(candidate, "associated_galaxy_distance")
            else ""
        ),
    }

    return info_dict


def sanatize_XRT_source_info(source) -> Dict[str, Any]:
    """
    Format XRT source information for display.

    Args:
        source: An XRT source object

    Returns:
        Formatted XRT source information as a dictionary
    """
    info_dict = {
        "Alert Identifier": source.get("alert_identifier", ""),
        "RA": source.get("right_ascension", ""),
        "Dec": source.get("declination", ""),
        "Significance": source.get("significance", ""),
        "URL": source.get("url", ""),
    }

    return info_dict


def by_chunk(items: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.

    Args:
        items: The list to split
        n: The size of each chunk

    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), n):
        chunks.append(items[i : i + n])
    return chunks
