import requests

url = "http://localhost:8000/api/v1/chat"
payload = {
    "message": "origin is MALPE. departure time is 8",
    "session_id": "test-session-999",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    data = response.json()
    print("Trip Context:", data.get("data", {}).get("trip_context"))
except Exception as e:
    print(e)
