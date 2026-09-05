"""Local offline geocoder for coastal ports, fishing harbors, and landing centers.

Supports:
- 100+ coastal landing centers and major/minor fishing harbors across India.
- Multilingual vernacular lookup (Hindi, Gujarati, Tamil, Kannada, Malayalam, Telugu, Bengali, Odia).
- Full backwards compatibility with COASTAL_PORTS_DB.
"""

import json
import os
import re
from typing import Tuple, Dict, Any, List, Optional

# Default paths to gazetteer GeoJSON files
GIS_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LANDING_CENTERS_PATH = os.path.join(GIS_DATA_DIR, "coastal_landing_centers.geojson")
PORTS_HARBORS_PATH = os.path.join(GIS_DATA_DIR, "coastal_ports_harbors.geojson")

# Legacy lookup table for Indian coastal ports (guarantees 100% backward compatibility)
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
    "rameswaram": (9.28, 79.31),
    "gulf of mannar": (9.15, 79.20),
}


class CoastalGazetteer:
    """Indexed gazetteer combining static ports, landing centers, and harbor layers."""

    def __init__(self):
        self._lookup: Dict[str, Tuple[float, float]] = dict(COASTAL_PORTS_DB)
        self._metadata_index: List[Dict[str, Any]] = []
        self._loaded: bool = False
        self._load_gazetteers()

    def _clean_name(self, name: str) -> str:
        """Strip suffixes like 'fishing harbor', 'port', 'jetty', etc."""
        cleaned = name.lower()
        cleaned = re.sub(r"\b(fishing|harbor|harbour|port|jetty|bunder|wharf|landing center|center)\b", "", cleaned)
        return " ".join(cleaned.split())

    def _load_gazetteers(self):
        if self._loaded:
            return

        # 1. Load Landing Centers
        if os.path.exists(LANDING_CENTERS_PATH):
            try:
                with open(LANDING_CENTERS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for feature in data.get("features", []):
                    geom = feature.get("geometry", {})
                    props = feature.get("properties", {})
                    coords = geom.get("coordinates")
                    if not coords or len(coords) < 2:
                        continue
                    # GeoJSON is [lon, lat] -> store (lat, lon)
                    lat, lon = float(coords[1]), float(coords[0])
                    name = props.get("name", "").strip()
                    if not name:
                        continue

                    norm_name = name.lower()
                    if norm_name not in self._lookup:
                        self._lookup[norm_name] = (lat, lon)

                    clean = self._clean_name(name)
                    if clean and clean not in self._lookup:
                        self._lookup[clean] = (lat, lon)

                    # Vernacular scripts (gu, hi, ta, kn, ml, te, bn, or)
                    vernacular = props.get("vernacular_names", {})
                    if isinstance(vernacular, dict):
                        for lang, vname in vernacular.items():
                            if vname and isinstance(vname, str):
                                v_norm = vname.strip().lower()
                                if v_norm not in self._lookup:
                                    self._lookup[v_norm] = (lat, lon)

                    self._metadata_index.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "state": props.get("state"),
                        "district": props.get("district"),
                        "facility_type": props.get("facility_type", "Landing Center"),
                        "vernacular_names": vernacular,
                    })
            except Exception as e:
                pass

        # 2. Load Ports & Harbors
        if os.path.exists(PORTS_HARBORS_PATH):
            try:
                with open(PORTS_HARBORS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for feature in data.get("features", []):
                    geom = feature.get("geometry", {})
                    props = feature.get("properties", {})
                    coords = geom.get("coordinates") or props.get("coordinates")
                    if not coords or len(coords) < 2:
                        continue
                    lat, lon = float(coords[1]), float(coords[0])
                    name = props.get("name", "").strip()
                    if not name:
                        continue

                    norm_name = name.lower()
                    if norm_name not in self._lookup:
                        self._lookup[norm_name] = (lat, lon)

                    clean = self._clean_name(name)
                    if clean and clean not in self._lookup:
                        self._lookup[clean] = (lat, lon)

                    self._metadata_index.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "state": props.get("state"),
                        "harbour_type": props.get("harbour_type", "Harbor"),
                    })
            except Exception as e:
                pass

        self._loaded = True

    def resolve(self, location_name: str) -> Tuple[float, float]:
        if not location_name or not location_name.strip():
            raise ValueError("Location name cannot be empty")

        query = location_name.strip().lower()

        # 1. Exact match
        if query in self._lookup:
            return self._lookup[query]

        # 2. Cleaned exact match
        clean_query = self._clean_name(query)
        if clean_query in self._lookup:
            return self._lookup[clean_query]

        # 3. Substring match
        for key, coords in self._lookup.items():
            if key in query or query in key:
                return coords

        # 4. Partial word match
        query_words = set(clean_query.split())
        if query_words:
            for key, coords in self._lookup.items():
                key_words = set(key.split())
                if query_words.issubset(key_words) or key_words.issubset(query_words):
                    return coords

        sample_names = sorted(set(list(COASTAL_PORTS_DB.keys())))
        raise ValueError(
            f"Unknown location '{location_name}'. Local geocoder supports 100+ coastal ports and landing centers including: "
            f"{', '.join(sample_names[:12])}..."
        )

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search coastal locations for auto-completion or frontend search."""
        if not query or not query.strip():
            return self._metadata_index[:limit]

        q = query.strip().lower()
        results = []
        for item in self._metadata_index:
            name = item.get("name", "").lower()
            state = (item.get("state") or "").lower()
            district = (item.get("district") or "").lower()
            vernacular_values = [str(v).lower() for v in item.get("vernacular_names", {}).values()]

            if q in name or q in state or q in district or any(q in v for v in vernacular_values):
                results.append(item)
                if len(results) >= limit:
                    break

        return results


# Global singleton instance
_gazetteer_instance = CoastalGazetteer()


def geocode(location_name: str) -> Tuple[float, float]:
    """
    Resolve a location name into (lat, lon).
    Searches local coastal landing centers, ports gazetteers, and legacy ports.

    Args:
        location_name: Name of port or landing center (e.g. 'Cochin', 'Mangalore', 'Munambam', 'वेरावल')

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        ValueError: If location is unknown or empty.
    """
    return _gazetteer_instance.resolve(location_name)


def search_locations(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search coastal locations with metadata."""
    return _gazetteer_instance.search(query, limit=limit)

