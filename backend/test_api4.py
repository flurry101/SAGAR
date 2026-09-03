import requests
import time

url = "http://localhost:8000/api/v1/chat"
payload = {
    "message": "I want to go fishing, is it safe?",
    "session_id": "test-session-hang",
    "language": "en"
}

start = time.time()
try:
    print("Sending request...")
    response = requests.post(url, json=payload, timeout=90)
    data = response.json()
    print(f"Time taken: {time.time() - start:.2f}s")
    print("Response Status:", data.get("status"))
except Exception as e:
    print(f"Error after {time.time() - start:.2f}s: {e}")
