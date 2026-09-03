import requests

url = "http://localhost:8000/api/v1/chat"
payload = {
    "message": "WHAT IS LOCAL NAVIGATION DATA MEANS",
    "session_id": "test-session-1234",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.json())
except Exception as e:
    print(e)
