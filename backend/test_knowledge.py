import requests

url = "http://localhost:8000/api/v1/chat"
session_id = "test-knowledge-bug-1"

vessel_profile = {
    "vessel_id": "vessel-trawler-45",
    "vessel_type": "Mechanized Trawler",
    "beam_width_m": 4.5,
    "length_m": 14.5,
    "cruising_speed_kmh": 15.0,
    "registration_number": "IND-KA-04-MM-8821",
    "home_port": "Mangalore Old Port"
}

print("--- Step 1: Initial query ---")
payload1 = {
    "message": "Planning trip from Malpe at 6 AM, 4 hours fishing, return at 4 PM",
    "session_id": session_id,
    "language": "en",
    "vessel_profile": vessel_profile
}
res1 = requests.post(url, json=payload1)
print(res1.status_code, res1.json().get('data', {}).get('workflow_status'))
print("Overall risk:", res1.json().get('data', {}).get('overall_risk_level'))

print("\n--- Step 2: Knowledge Question ---")
url_continue = "http://localhost:8000/api/v1/trip/continue"
payload2 = {
    "message": "WHAT MAI RESON FOR RISK",
    "session_id": session_id,
    "language": "en"
}
res2 = requests.post(url_continue, json=payload2)
print(res2.status_code, res2.json().get('data', {}).get('workflow_status'))

# Print what the advisory was!
print("\nResponse:")
print(res2.json().get('data', {}).get('advisory', {}).get('recommendation_text'))
