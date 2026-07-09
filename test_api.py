import requests
import json

try:
    url = "http://127.0.0.1:5001/api/details/INFY.NS"
    print(f"Requesting: {url}")
    resp = requests.get(url, timeout=30)
    
    if resp.status_code == 200:
        data = resp.json()
        print("SUCCESS! API is reachable.")
        print(f"Fundamentals Keys: {len(data.get('fundamentals', {}))}")
        print(f"News Items: {len(data.get('news', []))}")
    else:
        print(f"FAILED: Status {resp.status_code}")
        print(resp.text)
except Exception as e:
    print(f"EXCEPTION: {e}")
