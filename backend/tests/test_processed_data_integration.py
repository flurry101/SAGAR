"""
Tests for Processed Data Integration:
- Multilingual & Multi-Port Geocoding
- Multi-Layer Spatial Geofencing (MPAs, IMBL, Naval zones, Habitats)
- RAG Ingestion of JSON Policy Chunk Corpora & In-Memory Retrieval
"""

import pytest
from app.gis.geocoder import geocode, search_locations
from app.gis.geofence import check_geofence, load_restricted_zones
from app.gis.schemas import Waypoint
from app.chatbot.rag.ingestion import load_documents
from app.chatbot.retrieval.retriever import get_retriever, KnowledgeDomain
from app.chatbot.tools.knowledge_tools import search_marine_knowledge


# ==============================================================================
# 1. Multilingual & Multi-Port Geocoder Tests
# ==============================================================================

def test_legacy_port_geocoding_compatibility():
    """Verify that all standard coastal ports still resolve with identical coordinates."""
    lat, lon = geocode("cochin")
    assert round(lat, 2) == 9.97
    assert round(lon, 2) == 76.24

    lat, lon = geocode("mangalore")
    assert round(lat, 2) == 12.91
    assert round(lon, 2) == 74.86

    lat, lon = geocode("visakhapatnam")
    assert round(lat, 2) == 17.69
    assert round(lon, 2) == 83.22


def test_landing_centers_geocoding():
    """Verify newly adapted landing centers resolve correctly."""
    # Veraval (Gujarat)
    lat, lon = geocode("Veraval")
    assert 20.8 <= lat <= 21.0
    assert 70.3 <= lon <= 70.5

    # Porbandar (Gujarat)
    lat, lon = geocode("Porbandar")
    assert 21.5 <= lat <= 21.8
    assert 69.5 <= lon <= 69.8

    # Munambam (Kerala)
    lat, lon = geocode("Munambam")
    assert 10.1 <= lat <= 10.3
    assert 76.1 <= lon <= 76.3

    # Malpe (Karnataka)
    lat, lon = geocode("Malpe")
    assert 13.3 <= lat <= 13.5
    assert 74.6 <= lon <= 74.8


def test_vernacular_multilingual_geocoding():
    """Verify native Indian script queries resolve accurately."""
    # Gujarati for Veraval: વેરાવળ
    lat, lon = geocode("વેરાવળ")
    assert 20.8 <= lat <= 21.0
    assert 70.3 <= lon <= 70.5

    # Hindi for Veraval: वेरावल
    lat, lon = geocode("वेरावल")
    assert 20.8 <= lat <= 21.0
    assert 70.3 <= lon <= 70.5

    # Malayalam for Munambam: മുനമ്പം
    lat, lon = geocode("മുനമ്പം")
    assert 10.1 <= lat <= 10.3
    assert 76.1 <= lon <= 76.3

    # Kannada for Malpe: ಮಲ್ಪೆ
    lat, lon = geocode("ಮಲ್ಪೆ")
    assert 13.3 <= lat <= 13.5
    assert 74.6 <= lon <= 74.8


def test_gazetteer_search():
    """Test auto-complete/search across gazetteer."""
    results = search_locations("kerala", limit=5)
    assert len(results) > 0
    assert any(r.get("state") == "Kerala" for r in results)


# ==============================================================================
# 2. Multi-Layer Spatial Geofencing Tests
# ==============================================================================

def test_load_all_active_layers():
    """Verify that multi-layer loader loads zones from all active GeoJSON files."""
    zones = load_restricted_zones()
    assert len(zones) >= 5

    zone_ids = [z["zone_id"] for z in zones]
    # Check Naval, MPA, IMBL are present
    assert any("NAVAL" in zid or "NAV" in zid for zid in zone_ids)
    assert any("MPA" in zid for zid in zone_ids)
    assert any("IMBL" in zid for zid in zone_ids)


def test_naval_zone_geofence_violation():
    """Waypoint inside Kochi Naval Zone triggers violation."""
    wp_inside = Waypoint(lat=9.94, lon=76.20, timestamp="2026-09-01T05:00:00Z", leg_label="outbound")
    violations = check_geofence([wp_inside])
    assert len(violations) >= 1
    assert any("Naval" in v["restriction_type"] or "NAVAL" in v["zone_id"] for v in violations)


def test_gulf_of_mannar_mpa_violation():
    """Waypoint inside Gulf of Mannar Marine National Park triggers MPA violation."""
    wp_mpa = Waypoint(lat=9.10, lon=78.90, timestamp="2026-09-01T07:00:00Z", leg_label="fishing")
    violations = check_geofence([wp_mpa])
    assert len(violations) >= 1
    mpa_viol = next((v for v in violations if "MPA" in v["zone_id"] or "Mannar" in v["zone_name"]), None)
    assert mpa_viol is not None
    assert "Mannar" in mpa_viol["zone_name"]


def test_imbl_border_buffer_alert():
    """Waypoint near Indo-Sri Lanka maritime border triggers IMBL alert."""
    wp_imbl = Waypoint(lat=9.50, lon=79.45, timestamp="2026-09-01T08:00:00Z", leg_label="return")
    violations = check_geofence([wp_imbl])
    assert len(violations) >= 1
    imbl_viol = next((v for v in violations if "IMBL" in v["zone_id"] or "Border" in v["zone_name"] or "Maritime Boundary" in v["zone_name"]), None)
    assert imbl_viol is not None



# ==============================================================================
# 3. RAG Policy Chunks Ingestion & Retrieval Tests
# ==============================================================================

def test_load_documents_includes_policy_chunks():
    """Verify ingestion pipeline loads both markdown and json policy chunks."""
    docs = load_documents()
    assert len(docs) > 10

    policy_docs = [d for d in docs if "maritime_policy_chunks.json" in d["source"]]
    assert len(policy_docs) == 12  # All 12 chunks loaded

    # Check first chunk metadata
    chunk1 = next((d for d in policy_docs if "ORCA-RAG-0001" in d["source"]), None)
    assert chunk1 is not None
    assert "Monsoon" in chunk1["content"]
    assert chunk1["metadata"]["authority"] == "Department of Fisheries, GoI"


def test_in_memory_retrieval_monsoon_ban():
    """Verify retrieval returns accurate uniform monsoon ban policy details."""
    retriever = get_retriever(domain=KnowledgeDomain.REGULATIONS, top_k=3)
    results = retriever.invoke("When is the annual monsoon fishing ban on the West Coast?")
    assert len(results) > 0

    combined_text = " ".join([r.page_content for r in results])
    assert "June 1" in combined_text or "31st July" in combined_text or "61-day" in combined_text


def test_in_memory_retrieval_distress_vhf16():
    """Verify retrieval returns Coast Guard VHF 16 SOP and emergency numbers."""
    retriever = get_retriever(domain=KnowledgeDomain.SAFETY, top_k=3)
    results = retriever.invoke("What is the emergency VHF channel and Coast Guard helpline number?")
    assert len(results) > 0

    combined_text = " ".join([r.page_content for r in results])
    assert "16" in combined_text
    assert "1554" in combined_text or "MAYDAY" in combined_text or "Distress" in combined_text


def test_in_memory_retrieval_wildlife_protection_act():
    """Verify retrieval returns Schedule I protected taxa (corals, dugongs, turtles)."""
    retriever = get_retriever(domain=KnowledgeDomain.ALL, top_k=3)
    results = retriever.invoke("Which marine species are protected under Schedule I of the Wildlife Protection Act?")
    assert len(results) > 0

    combined_text = " ".join([r.page_content for r in results])
    assert "Schedule I" in combined_text
    assert "Turtle" in combined_text or "Coral" in combined_text or "Dugong" in combined_text or "Whale Shark" in combined_text


def test_knowledge_tool_search_marine_knowledge():
    """Verify search_marine_knowledge tool produces formatted grounded responses with citations."""
    response = search_marine_knowledge.invoke({"query": "What is the territorial waters limit under the Maritime Zones Act?"})
    assert "12 nautical miles" in response or "Territorial" in response
    assert "[Source:" in response
