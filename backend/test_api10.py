import requests

url = "http://localhost:8000/api/v1/chat"
payload = {
    "message": "Planning trip from Malpe at 6 AM, 4 hours fishing, return at 4 PM",
    "session_id": "sess-12345",
    "thread_id": "thread-12345",
    "language": "en",
    "vessel_profile": {
        "vessel_id": "vessel-trawler-45",
        "vessel_type": "Mechanized Trawler",
        "beam_width_m": 4.5,
        "length_m": 14.5,
        "cruising_speed_kmh": 15.0,
        "registration_number": "IND-KA-04-MM-8821",
        "home_port": "Mangalore Old Port"
    }
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.text)
except Exception as e:
    print("Error:", e)
