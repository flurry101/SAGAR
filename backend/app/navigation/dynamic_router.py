"""Traffic-aware routing extension point; routing engine integration is intentionally deferred."""
from typing import Iterable, Mapping, Sequence


def route_around_traffic(waypoints: Sequence[Mapping], traffic_features: Iterable[Mapping], safety_radius_nm: float = 1.0):
    """Return the proposed route unchanged until an operational route engine is attached.

    Keeping this deterministic stub isolates future obstacle-avoidance policy from AIS ingestion.
    """
    del traffic_features, safety_radius_nm
    return list(waypoints)
