import requests

url = "http://localhost:8000/api/v1/trip/continue"
payload = {
    "message": "Planning trip from Malpe at 6 AM, 4 hours fishing, return at 4 PM",
    "session_id": "test-session-not-found",
    "thread_id": "test-thread",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response JSON:", response.text)
except Exception as e:
    print("Error:", e)
