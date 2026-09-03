import requests

url = "http://localhost:8000/api/v1/chat"
headers = {
    "Origin": "http://127.0.0.1:5173",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}

try:
    res = requests.options(url, headers=headers)
    print(res.status_code)
    print(res.text)
except Exception as e:
    print("Error:", e)
