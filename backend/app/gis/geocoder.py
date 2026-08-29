"""Local offline geocoder for coastal ports and maritime locations."""

from typing import Tuple, Dict

# Local lookup table for Indian coastal ports and maritime hubs
COASTAL_PORTS_DB: Dict[str, Tuple[float, float]] = {
    "cochin": (9.9674, 76.2429),
    "kochi": (9.9674, 76.2429),
    "mangalore": (12.9141, 74.8560),
    "chennai": (13.0827, 80.2707),
    "mumbai": (18.9438, 72.8360),
    "visakhapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "tuticorin": (8.7642, 78.1348),
    "thoothukudi": (8.7642, 78.1348),
    "goa": (15.4909, 73.8278),
    "mormugao": (15.4124, 73.8055),
    "kakinada": (16.9891, 82.2475),
    "paradeep": (20.2644, 86.6698),
    "paradip": (20.2644, 86.6698),
    "kollam": (8.8932, 76.5847),
    "quilon": (8.8932, 76.5847),
    "veraval": (20.9000, 70.3667),
    "porbandar": (21.6417, 69.6293),
    "haldia": (22.0667, 88.0667),
    "port blair": (11.6234, 92.7264),
}


def geocode(location_name: str) -> Tuple[float, float]:
    """
    Resolve a location name into (lat, lon).
    Pure deterministic lookup against local coastal port dictionary.

    Args:
        location_name: Name of port or location (e.g. 'Cochin', 'Mangalore')

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If location is unknown or empty.
    """
    if not location_name or not location_name.strip():
        raise ValueError("Location name cannot be empty")

    normalized = location_name.strip().lower()
    if normalized in COASTAL_PORTS_DB:
        return COASTAL_PORTS_DB[normalized]

    # Partial match check
    for key, coords in COASTAL_PORTS_DB.items():
        if key in normalized or normalized in key:
            return coords

    raise ValueError(
        f"Unknown location '{location_name}'. Local geocoder supports ports: "
        f"{', '.join(sorted(set(COASTAL_PORTS_DB.keys())))}"
    )
