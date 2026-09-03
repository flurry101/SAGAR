import requests
import time

url = "http://localhost:8000/api/v1/chat"
session_id = "test-followup-123"

# Step 1: Initial trip plan
print("--- Step 1: Trip Plan ---")
payload1 = {
    "message": "I want to go fishing from Malpe at 5 AM",
    "session_id": session_id,
    "language": "en"
}
res1 = requests.post(url, json=payload1)
print(res1.status_code, res1.json().get('status'))

# Step 2: Clarification
print("--- Step 2: Clarification ---")
url_continue = "http://localhost:8000/api/v1/trip/continue"
payload2 = {
    "message": "beam is 4.5m, speed is 15",
    "session_id": session_id,
    "language": "en"
}
res2 = requests.post(url_continue, json=payload2)
print(res2.status_code, res2.json().get('status'))

# Step 3: Follow-up Knowledge Question
print("--- Step 3: Knowledge Question ---")
payload3 = {
    "message": "what is local navigation data means",
    "session_id": session_id,
    "language": "en"
}
t0 = time.time()
res3 = requests.post(url, json=payload3)
print(f"Time taken: {time.time() - t0:.2f}s")
print(res3.status_code)
print(res3.text)
