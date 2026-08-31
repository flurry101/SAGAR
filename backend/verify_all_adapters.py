"""
verify_all_adapters.py
======================
M4 verification: Test all 7 adapters (6 existing + 2 new) at standard test points.

Test locations:
    Mangalore: 12.87°N, 74.86°E
    Veraval:   21.66°N, 70.37°E
    Vizag:     17.69°N, 83.30°E

Adapters to test:
    1. OpenMeteoAdapter (wave, wind, SST, ocean current)
    2. SSTAdapter (sea surface temperature)
    3. StaticHazardAdapter (cyclones)
    4. StaticPFZAdapter (fishing zones + chlorophyll)
    5. AmfitriteHABAdapter (harmful algal blooms)
    6. TideAdapter (NEW - tides)
    7. GEBCOAdapter (NEW - bathymetry)
"""
from datetime import datetime, timezone
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from typing import Dict, Any, List, Tuple

from app.adapters.open_meteo_adapter import OpenMeteoAdapter
from app.adapters.sst_adapter import SSTAdapter
from app.adapters.static_hazard_adapter import StaticHazardAdapter
from app.adapters.static_pfz_adapter import StaticPFZAdapter
from app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter
from app.adapters.tide_adapter import TideAdapter
from app.adapters.gebco_adapter import GEBCOAdapter

# Test locations
TEST_POINTS = {
    "Mangalore": (12.87, 74.86),
    "Veraval":   (21.66, 70.37),
    "Vizag":     (17.69, 83.30),
}

# Initialize adapters
adapters = {
    "OpenMeteo":      OpenMeteoAdapter(),
    "SST":            SSTAdapter(),
    "Hazards":        StaticHazardAdapter(),
    "PFZ":            StaticPFZAdapter(),
    "HAB":            AmfitriteHABAdapter(),
    "Tide":           TideAdapter(),
    "GEBCO":          GEBCOAdapter(),
}


def test_adapter(adapter_name: str, adapter, lat: float, lon: float, time_iso: str) -> Dict[str, Any]:
    """Test a single adapter at a point. Return pass/fail + details."""
    try:
        if adapter_name == "PFZ":
            result = adapter.fetch_data(lat, lon, time_iso, radius_km=100.0)
            resolved = result.get("resolved", False)
            status = result.get("status", "unknown")
        elif adapter_name == "Tide":
            result = adapter.fetch_data(lat, lon, time_iso)
            resolved = result.get("resolved", False)
            status = result.get("status", "unknown")
            depth = result.get("tide_height_m", "N/A")
            return {
                "adapter": adapter_name,
                "lat": lat,
                "lon": lon,
                "passed": resolved,
                "live_source_confirmed": result.get("provenance", {}).get("fallback_tier") == 1,
                "source": result.get("provenance", {}).get("source"),
                "status": status,
                "fallback_tier": result.get("provenance", {}).get("fallback_tier", "unknown"),
                "tide_height_m": depth,
                "error": None,
            }
        elif adapter_name == "GEBCO":
            result = adapter.fetch_data(lat, lon, time_iso)
            resolved = result.get("resolved", False)
            status = result.get("status", "unknown")
            depth = result.get("depth_m", "N/A")
            return {
                "adapter": adapter_name,
                "lat": lat,
                "lon": lon,
                "passed": resolved,
                "live_source_confirmed": result.get("provenance", {}).get("fallback_tier") == 1,
                "source": result.get("provenance", {}).get("source"),
                "status": status,
                "fallback_tier": result.get("provenance", {}).get("fallback_tier", "unknown"),
                "depth_m": depth,
                "error": None,
            }
        else:
            result = adapter.fetch_data(lat, lon, time_iso)
            resolved = result.get("resolved", True)  # Default True if key missing
            status = result.get("status", "unknown")

        return {
            "adapter": adapter_name,
            "lat": lat,
            "lon": lon,
            "passed": resolved,
            "live_source_confirmed": result.get("provenance", {}).get("fallback_tier") == 1,
            "source": result.get("provenance", {}).get("source"),
            "status": status,
            "fallback_tier": result.get("provenance", {}).get("fallback_tier", "unknown"),
            "error": None,
        }

    except Exception as e:
        return {
            "adapter": adapter_name,
            "lat": lat,
            "lon": lon,
            "passed": False,
            "status": "error",
            "error": str(e)[:100],
        }


def main():
    """Run full verification suite."""
    time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print("=" * 80)
    print("M4 ADAPTER VERIFICATION — All Adapters at Standard Test Points")
    print("=" * 80)
    print(f"\nTest time: {time_iso}")
    print(f"Test points: {', '.join(TEST_POINTS.keys())}")
    print(f"Adapters: {', '.join(adapters.keys())}\n")

    results: List[Dict[str, Any]] = []

    for location_name, (lat, lon) in TEST_POINTS.items():
        print(f"\n{location_name} ({lat}°N, {lon}°E)")
        print("-" * 60)

        for adapter_name, adapter in adapters.items():
            result = test_adapter(adapter_name, adapter, lat, lon, time_iso)
            results.append(result)

            status_icon = "[OK]  " if result["passed"] else "[FAIL]"
            fallback = f" [Tier {result.get('fallback_tier', '?')}]" if result.get("fallback_tier") else ""
            live_marker = " LIVE" if result.get("live_source_confirmed") else " FALLBACK"
            extra = ""
            if "tide_height_m" in result:
                extra = f" (tide: {result['tide_height_m']}m)"
            elif "depth_m" in result:
                extra = f" (depth: {result['depth_m']}m)"
            elif adapter_name == "PFZ" and result.get("source"):
                extra = f" - {result['source']}"


            print(f"  {status_icon} {adapter_name:15} {result['status']:12}{fallback}{live_marker}{extra}")
            if result.get("error"):
                print(f"      Error: {result['error']}")

    # Summary table
    print("\n" + "=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)

    pass_count = sum(1 for r in results if r["passed"])
    total_count = len(results)

    print(f"\nTotal tests: {total_count}")
    print(f"Passed: {pass_count} ({100*pass_count//total_count}%)")
    print(f"Failed: {total_count - pass_count}")

    # Adapter summary
    print("\nBy adapter:")
    for adapter_name in adapters.keys():
        adapter_results = [r for r in results if r["adapter"] == adapter_name]
        adapter_passed = sum(1 for r in adapter_results if r["passed"])
        adapter_total = len(adapter_results)
        status_icon = "[OK]  " if adapter_passed == adapter_total else "[WARN]"
        print(f"  {status_icon} {adapter_name:15} {adapter_passed}/{adapter_total} passed")

    return pass_count == total_count


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
