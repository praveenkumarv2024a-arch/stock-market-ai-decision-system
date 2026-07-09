import requests
import json

try:
    print("Testing API on Port 5004...")
    url = "http://127.0.0.1:5004/api/paper/funds"
    headers = {"Content-Type": "application/json"}
    data = {"amount": 100}
    
    resp = requests.post(url, json=data, timeout=5)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
    
except Exception as e:
    print(f"Error: {e}")
