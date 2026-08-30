# verify_all_live_and_fallbacks.py
import sys
import json
import traceback
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import httpx

from backend.app.adapters.open_meteo_adapter import OpenMeteoAdapter
from backend.app.adapters.sst_adapter import SSTAdapter
from backend.app.adapters.static_hazard_adapter import StaticHazardAdapter
from backend.app.adapters.static_pfz_adapter import StaticPFZAdapter
from backend.app.adapters.amfitrite_hab_adapter import AmfitriteHABAdapter

def get_current_utc_timestamp() -> str:
    # 3 hours in future to simulate a waypoint ETA
    dt = datetime.now(timezone.utc) + timedelta(hours=3)
    return dt.strftime("%Y-%m-%dT%H:00:00Z")

def run_live_verification():
    print("\n" + "="*80)
    print("PART 2: LIVE END-TO-END VERIFICATION")
    print("="*80)

    # Instantiate adapters
    weather_adapter = OpenMeteoAdapter()
    sst_adapter = SSTAdapter()
    hazard_adapter = StaticHazardAdapter()
    pfz_adapter = StaticPFZAdapter()
    hab_adapter = AmfitriteHABAdapter()

    # Inject dummy model so HAB can run Tier 2 if cloud-free imagery exists
    try:
        import torch
        class DummyRDNet(torch.nn.Module):
            def forward(self, x):
                return torch.tensor([[0.9, 0.1]])
        hab_adapter.model = DummyRDNet()
        hab_adapter.model_loaded = True
    except Exception:
        pass

    test_points = [
        ("Mangalore", 12.87, 74.84),
        ("Veraval", 20.90, 70.37),
        ("Vizag", 17.68, 83.21),
    ]

    timestamp = get_current_utc_timestamp()
    print(f"Using target timestamp: {timestamp}")

    results = []

    for name, lat, lon in test_points:
        print(f"\n--- Testing Point: {name} (lat={lat}, lon={lon}) ---")
        
        # 1. Weather / Marine
        print("  Querying Weather/Marine (OpenMeteo)...")
        w_res = weather_adapter.fetch_data(lat, lon, timestamp)
        
        # 2. SST
        print("  Querying SST...")
        sst_res = sst_adapter.fetch_data(lat, lon, timestamp)

        # 3. Hazards
        print("  Querying Hazards (GDACS)...")
        haz_res = hazard_adapter.fetch_data(lat, lon, timestamp)

        # 4. PFZ
        print("  Querying PFZ (ERDDAP)...")
        pfz_res = pfz_adapter.fetch_data(lat, lon, radius_km=150.0)

        # 5. HAB
        print("  Querying HAB (Sentinel-2 STAC)...")
        hab_res = hab_adapter.fetch_data(lat, lon, timestamp)

        results.append({
            "point": name,
            "weather": w_res,
            "sst": sst_res,
            "hazards": haz_res,
            "pfz": pfz_res,
            "hab": hab_res
        })

    # Print out results summary table
    print("\n" + "="*80)
    print("PART 2 SUMMARY TABLE")
    print("="*80)
    print(f"{'Point':<10} | {'Adapter':<15} | {'Resolved':<8} | {'Tier':<4} | {'Confidence':<10} | {'Key Values/Source':<35}")
    print("-" * 95)
    for r in results:
        pt = r["point"]
        
        # Weather
        w = r["weather"]
        w_val = f"waves={w.get('wave_height_m')}m, wind={w.get('wind_speed_kmh')}kmh"
        print(f"{pt:<10} | {'Weather/Marine':<15} | {str(w.get('resolved')):<8} | {w.get('provenance', {}).get('fallback_tier'):<4} | {w.get('provenance', {}).get('confidence'):<10} | {w_val:<35}")
        
        # SST
        s = r["sst"]
        s_val = f"sst={s.get('sst_celsius')} C"
        print(f"{pt:<10} | {'SST':<15} | {str(s.get('resolved')):<8} | {s.get('provenance', {}).get('fallback_tier'):<4} | {s.get('provenance', {}).get('confidence'):<10} | {s_val:<35}")

        # Hazards
        h = r["hazards"]
        h_val = f"hazards={len(h.get('hazards', []))}, cyclone_active={h.get('cyclone_active')}"
        print(f"{pt:<10} | {'GDACS Hazards':<15} | {str(h.get('resolved')):<8} | {h.get('provenance', {}).get('fallback_tier'):<4} | {h.get('provenance', {}).get('confidence'):<10} | {h_val:<35}")

        # PFZ
        p = r["pfz"]
        p_val = f"pfzs={len(p.get('pfzs', []))}"
        print(f"{pt:<10} | {'NOAA PFZ':<15} | {str(p.get('resolved')):<8} | {p.get('provenance', {}).get('fallback_tier'):<4} | {p.get('provenance', {}).get('confidence'):<10} | {p_val:<35}")

        # HAB
        hb = r["hab"]
        hb_val = f"prob={hb.get('hab_probability')}, detected={hb.get('hab_detected')}"
        print(f"{pt:<10} | {'Sentinel-2 HAB':<15} | {str(hb.get('resolved')):<8} | {hb.get('provenance', {}).get('fallback_tier'):<4} | {hb.get('provenance', {}).get('confidence'):<10} | {hb_val:<35}")
        print("-" * 95)


def run_fallback_verification():
    print("\n" + "="*80)
    print("PART 3: FORCED FALLBACK DEGRADATION TEST")
    print("="*80)

    # 1. Weather / Marine (OpenMeteoAdapter)
    print("\n--- 1. Weather Fallback Test (Simulate httpx timeout) ---")
    weather_adapter = OpenMeteoAdapter()
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Mocked Weather Timeout")):
        res = weather_adapter.fetch_data(12.87, 74.84, get_current_utc_timestamp())
    prov = res.get("provenance", {})
    print(f"Resolved: {res.get('resolved')}")
    print(f"Fallback Tier: {prov.get('fallback_tier')}")
    print(f"Confidence: {prov.get('confidence')}")
    print(f"Source: {prov.get('source')}")
    print(f"Wave Height: {res.get('wave_height_m')}m")

    # 2. SST (SSTAdapter)
    print("\n--- 2. SST Fallback Test (Simulate API error/null response) ---")
    sst_adapter = SSTAdapter()
    with patch("httpx.Client.get", side_effect=httpx.HTTPError("Mocked SST API Failure")):
        res = sst_adapter.fetch_data(12.87, 74.84, get_current_utc_timestamp())
    prov = res.get("provenance", {})
    print(f"Resolved: {res.get('resolved')}")
    print(f"Fallback Tier: {prov.get('fallback_tier')}")
    print(f"Confidence: {prov.get('confidence')}")
    print(f"Source: {prov.get('source')}")
    print(f"SST Climatology Value: {res.get('sst_celsius')} C")

    # 3. GDACS Hazards (StaticHazardAdapter)
    print("\n--- 3. Hazards Fallback Test (Simulate GDACS API failure) ---")
    hazard_adapter = StaticHazardAdapter()
    with patch("httpx.Client.get", side_effect=httpx.HTTPError("Mocked GDACS Failure")):
        res = hazard_adapter.fetch_data(12.87, 74.84, get_current_utc_timestamp())
    prov = res.get("provenance", {})
    print(f"Resolved: {res.get('resolved')}")
    print(f"Fallback Tier: {prov.get('fallback_tier')}")
    print(f"Confidence: {prov.get('confidence')}")
    print(f"Source: {prov.get('source')}")
    print(f"Hazard alerts returned: {len(res.get('hazards', []))}")

    # 4. HAB (AmfitriteHABAdapter)
    print("\n--- 4. HAB Fallback Test (Simulate no cloud-free images / STAC empty) ---")
    hab_adapter = AmfitriteHABAdapter()
    with patch("httpx.post") as mock_post:
        # Mock empty STAC response
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"features": []}
        mock_post.return_value = resp
        res = hab_adapter.fetch_data(12.87, 74.84, get_current_utc_timestamp())
    prov = res.get("provenance", {})
    print(f"Resolved: {res.get('resolved')}")
    print(f"Fallback Tier: {prov.get('fallback_tier')}")
    print(f"Confidence: {prov.get('confidence')}")
    print(f"Source: {prov.get('source')}")
    print(f"HAB Detected: {res.get('hab_detected')}")
    print(f"Probability: {res.get('hab_probability')}")

    # 5. PFZ (StaticPFZAdapter)
    print("\n--- 5. PFZ Fallback Test (Simulate ERDDAP server failure) ---")
    pfz_adapter = StaticPFZAdapter()
    with patch("httpx.Client.get", side_effect=httpx.HTTPError("Mocked ERDDAP Failure")):
        res = pfz_adapter.fetch_data(12.87, 74.84, radius_km=150.0)
    prov = res.get("provenance", {})
    print(f"Resolved: {res.get('resolved')}")
    print(f"Fallback Tier: {prov.get('fallback_tier')}")
    print(f"Confidence: {prov.get('confidence')}")
    print(f"Source: {prov.get('source')}")
    print(f"PFZ features returned: {len(res.get('pfzs', []))}")


if __name__ == "__main__":
    run_live_verification()
    run_fallback_verification()
