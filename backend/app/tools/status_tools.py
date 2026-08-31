"""
Consolidated adapter health status summary
==========================================

This module provides a single entry point to query the health/status
of all 7 marine data adapters.

Usage:
    from app.status_tools import get_adapter_health_status
    health = get_adapter_health_status()
    # Returns dict with adapter_name -> {tier, confidence, last_retrieved_at}
"""

from datetime import datetime, timezone
from typing import Dict, Any
import logging

from app.adapters.open_meteo_adapter import OpenMeteoAdapter
from app.adapters.sst_adapter import SSTAdapter
from app.adapters.static_hazard_adapter import StaticHazardAdapter
from app.adapters.static_pfz_adapter import StaticPFZAdapter
from app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter
from app.adapters.tide_adapter import TideAdapter
from app.adapters.gebco_adapter import GEBCOAdapter

logger = logging.getLogger(__name__)

# Global adapter instances
_adapters = {
    "OpenMeteo": OpenMeteoAdapter(),
    "SST": SSTAdapter(),
    "Hazards": StaticHazardAdapter(),
    "PFZ": StaticPFZAdapter(),
    "HAB": AmfitriteHABAdapter(),
    "Tide": TideAdapter(),
    "GEBCO": GEBCOAdapter(),
}


def get_adapter_health_status() -> Dict[str, Dict[str, Any]]:
    """
    Query all adapters at a test location and return consolidated health status.

    Returns
    -------
    {
        "OpenMeteo": {
            "status": "healthy" | "degraded" | "offline",
            "fallback_tier": 1 | 2 | 3,
            "confidence": float (0.0 - 1.0),
            "last_error": str | None,
            "test_location": "12.87, 74.86",  # Mangalore
            "test_time": ISO 8601 UTC
        },
        ...
    }

    Notes:
        - Uses Mangalore (12.87°N, 74.86°E) as a stable test point.
        - Tests are lightweight (single point query, no spatial loops).
        - Status: "healthy" = Tier 1 + confidence >= 0.7,
                  "degraded" = Tier 3 or low confidence,
                  "offline" = exception or unresolvable
    """
    test_lat, test_lon = 12.87, 74.86  # Mangalore (stable coastal point)
    test_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: Dict[str, Dict[str, Any]] = {}

    for adapter_name, adapter in _adapters.items():
        try:
            # Fetch once; adapt parameters per adapter type
            if adapter_name == "PFZ":
                obs = adapter.fetch_data(test_lat, test_lon, test_time, radius_km=100.0)
            else:
                obs = adapter.fetch_data(test_lat, test_lon, test_time)

            # Parse provenance (may be dict or string representation)
            provenance = obs.get("provenance", {})
            if isinstance(provenance, str):
                import ast
                try:
                    provenance = ast.literal_eval(provenance)
                except (ValueError, SyntaxError):
                    provenance = {}
            
            resolved = obs.get("resolved", False)
            status_str = obs.get("status", "unknown")

            # Determine health status
            fallback_tier = provenance.get("fallback_tier", 3)
            confidence_raw = provenance.get("confidence", "UNKNOWN")
            
            # Convert confidence string to float
            if isinstance(confidence_raw, str):
                confidence_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3, "UNKNOWN": 0.0}
                confidence = confidence_map.get(confidence_raw.upper(), 0.0)
            else:
                confidence = float(confidence_raw) if confidence_raw else 0.0

            if resolved and fallback_tier == 1 and confidence >= 0.7:
                health_status = "healthy"
            elif resolved:
                health_status = "degraded"
            else:
                health_status = "offline"

            results[adapter_name] = {
                "status": health_status,
                "fallback_tier": fallback_tier,
                "confidence": confidence,
                "confidence_str": confidence_raw,
                "resolved": resolved,
                "api_status": status_str,
                "last_error": None,
                "test_location": f"{test_lat}, {test_lon}",
                "test_time": test_time,
                "source_name": provenance.get("source_name", provenance.get("source", "unknown")),
                "provenance": provenance,
            }

        except Exception as e:
            results[adapter_name] = {
                "status": "offline",
                "fallback_tier": 3,
                "confidence": 0.0,
                "resolved": False,
                "api_status": "error",
                "last_error": str(e)[:200],
                "test_location": f"{test_lat}, {test_lon}",
                "test_time": test_time,
                "source_name": "unknown",
                "provenance": {},
            }

    return results


def print_adapter_health_summary():
    """Pretty-print adapter health status."""
    health = get_adapter_health_status()

    print("\n" + "=" * 80)
    print("ADAPTER HEALTH STATUS SUMMARY")
    print("=" * 80)

    healthy_count = sum(1 for v in health.values() if v["status"] == "healthy")
    degraded_count = sum(1 for v in health.values() if v["status"] == "degraded")
    offline_count = sum(1 for v in health.values() if v["status"] == "offline")

    print(f"\nHealthy: {healthy_count}  Degraded: {degraded_count}  Offline: {offline_count}")
    print()

    for adapter_name, info in health.items():
        status_icon = "✓" if info["status"] == "healthy" else "⚠" if info["status"] == "degraded" else "✗"
        tier = info["fallback_tier"]
        conf = f"{info['confidence']:.1%}" if info["confidence"] else "N/A"
        source = info["source_name"][:20].ljust(20)

        print(f"  {status_icon} {adapter_name:15} Tier {tier}  Confidence: {conf}  Source: {source}")
        if info["last_error"]:
            print(f"      → Error: {info['last_error']}")


if __name__ == "__main__":
    print_adapter_health_summary()
