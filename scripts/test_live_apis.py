#!/usr/bin/env python3
"""
scripts/test_live_apis.py
=========================
Live API verification script for SAGAR.
Tests all endpoints including Health, LangGraph Gemini Agent, RAG Copilot,
Weather, Marine, Risk Engine, Vessel, User Profile, and Voice services.

Usage:
    python scripts/test_live_apis.py [BASE_URL]
    Example: python scripts/test_live_apis.py http://localhost:8000
"""

import sys
import json
import time
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_endpoint(client: httpx.Client, name: str, method: str, path: str, json_body: Dict[str, Any] = None, headers: Dict[str, str] = None) -> bool:
    url = f"{BASE_URL}{path}"
    start = time.time()
    try:
        if method.upper() == "GET":
            resp = client.get(url, headers=headers, timeout=30.0)
        else:
            resp = client.post(url, json=json_body, headers=headers, timeout=30.0)
        elapsed = round((time.time() - start) * 1000, 1)

        if resp.status_code in (200, 201):
            print(f"  \033[92m[PASS]\033[0m {name:<35} {resp.status_code} ({elapsed}ms)")
            return True
        else:
            print(f"  \033[91m[FAIL]\033[0m {name:<35} {resp.status_code} ({elapsed}ms) - {resp.text[:120]}")
            return False
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 1)
        print(f"  \033[91m[ERROR]\033[0m {name:<34} ({elapsed}ms) - {str(e)[:100]}")
        return False

def main():
    print_header(f"SAGAR LIVE API VERIFICATION SUITE — Target: {BASE_URL}")

    with httpx.Client() as client:
        results = []

        # 1. Health & Status
        print("\n[1] Health & System Probes")
        results.append(test_endpoint(client, "Root Status Probe", "GET", "/"))
        results.append(test_endpoint(client, "API Liveness Probe", "GET", "/api/v1/health"))
        results.append(test_endpoint(client, "API Readiness Probe", "GET", "/api/v1/ready"))

        # 2. Weather & Marine Live Adapters
        print("\n[2] Weather & Marine Live Adapters")
        results.append(test_endpoint(
            client, "Weather Forecast (OpenMeteo)", "POST", "/api/v1/weather/forecast",
            json_body={"waypoints": [{"waypoint_index": 0, "lat": 12.87, "lon": 74.84, "eta_iso": "2026-09-02T10:00:00Z"}]}
        ))
        results.append(test_endpoint(
            client, "Cyclone & Hazard Alerts", "POST", "/api/v1/weather/hazards",
            json_body={"bbox": {"lat_min": 10.0, "lat_max": 15.0, "lon_min": 72.0, "lon_max": 76.0}}
        ))
        results.append(test_endpoint(
            client, "INCOIS Potential Fishing Zones", "POST", "/api/v1/marine/pfz",
            json_body={"origin": {"lat": 12.87, "lon": 74.84}, "radius_km": 100.0}
        ))
        results.append(test_endpoint(
            client, "Marine Waves & SST", "POST", "/api/v1/marine/observations",
            json_body={"waypoints": [{"waypoint_index": 0, "lat": 12.87, "lon": 74.84, "eta_iso": "2026-09-02T10:00:00Z"}]}
        ))

        # 3. Deterministic Risk Engine
        print("\n[3] Deterministic Marine Risk Engine")
        results.append(test_endpoint(
            client, "Physics Risk Evaluation (SVAS)", "POST", "/api/v1/risk/evaluate",
            json_body={
                "vessel": {"beam_m": 4.5, "draft_m": 1.5, "length_m": 14.0},
                "environmental_observations": [{
                    "waypoint_index": 0,
                    "wave_height_m": 0.9,
                    "wind_speed_kmh": 22.0,
                    "depth_m": 25.0,
                    "tide_height_m": 0.5
                }]
            }
        ))

        # 4. LangGraph Multi-Agent Trip Planner & Gemini
        print("\n[4] LangGraph Multi-Agent & Gemini LLM")
        results.append(test_endpoint(
            client, "Trip Assess (Multi-Agent)", "POST", "/api/v1/trip/assess",
            json_body={
                "message": "Planning fishing trip from Mangalore at 5 AM tomorrow, returning at 2 PM.",
                "language": "en"
            }
        ))
        results.append(test_endpoint(
            client, "Chat Trip Planner Interface", "POST", "/api/v1/chat",
            json_body={
                "message": "Where is the nearest safe fishing zone?",
                "language": "en"
            }
        ))

        # 5. Copilot Knowledge RAG
        print("\n[5] Fisherman Copilot & RAG")
        results.append(test_endpoint(
            client, "Copilot Knowledge Retrieval", "POST", "/api/v1/copilot",
            json_body={"message": "What is a Potential Fishing Zone and how does INCOIS identify it?"}
        ))

        # 6. Vessel Specifications
        print("\n[6] Vessel Specifications")
        results.append(test_endpoint(client, "Get Vessel Profile", "GET", "/api/v1/vessel/vessel-001"))

        # 7. Voice Services
        print("\n[7] Multilingual Voice Services")
        results.append(test_endpoint(
            client, "Voice Text-to-Speech (TTS)", "POST", "/api/v1/voice/tts",
            json_body={"text": "Conditions are safe for navigation.", "language": "en"}
        ))
        results.append(test_endpoint(
            client, "Voice Query Agent", "POST", "/api/v1/voice/query",
            json_body={"query": "Is the sea calm tomorrow morning?", "language": "en"}
        ))

        # Summary
        passed = sum(1 for r in results if r)
        total = len(results)
        print_header(f"SUMMARY: {passed}/{total} ENDPOINTS PASSED ({round(100*passed/total)}%)")

if __name__ == "__main__":
    main()

