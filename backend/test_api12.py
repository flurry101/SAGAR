import requests
import time

url = "http://localhost:8000/api/v1/chat"
session_id = "test-ui-flow-5"

vessel_profile = {
    "vessel_id": "vessel-trawler-45",
    "vessel_type": "Mechanized Trawler",
    "beam_width_m": 4.5,
    "length_m": 14.5,
    "cruising_speed_kmh": 15.0,
    "registration_number": "IND-KA-04-MM-8821",
    "home_port": "Mangalore Old Port"
}

# Step 1: Initial query missing origin and time
print("--- Step 1: Missing Details ---")
payload1 = {
    "message": "I want to go fishing",
    "session_id": session_id,
    "language": "en",
    "vessel_profile": vessel_profile
}
res1 = requests.post(url, json=payload1)
print(res1.status_code, res1.json().get('status'), res1.json().get('data', {}).get('workflow_status'))

# Step 2: Provide details
print("--- Step 2: Provide Details ---")
url_continue = "http://localhost:8000/api/v1/trip/continue"
payload2 = {
    "message": "origin is MALPE. departure time iso is 2026-09-04T05:00:00Z",
    "session_id": session_id,
    "language": "en"
}
res2 = requests.post(url_continue, json=payload2)
print(res2.status_code, res2.json().get('status'), res2.json().get('data', {}).get('workflow_status'))

# Step 3: Follow-up Knowledge Question
print("--- Step 3: Knowledge Question ---")
payload3 = {
    "message": "what is local navigation data means",
    "session_id": session_id,
    "language": "en"
}
t0 = time.time()
res3 = requests.post(url_continue, json=payload3)
print(f"Time taken: {time.time() - t0:.2f}s")
print(res3.status_code, res3.json().get('status'), res3.json().get('data', {}).get('workflow_status'))
