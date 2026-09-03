import requests

url = "http://localhost:8000/api/v1/chat"
payload = {
    "message": "origin is MALPE. departure time iso is 8",
    "session_id": "test-session-5678",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    print(response.json())
except Exception as e:
    print(e)
