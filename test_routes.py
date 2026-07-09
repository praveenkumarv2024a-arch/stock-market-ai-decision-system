import requests

def test_route(name, url):
    try:
        print(f"Testing {name}: {url}")
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Handle list or dict returns
            count = len(data) if isinstance(data, list) else len(data.keys())
            print(f"PASS: {name} returned {count} items/keys.")
        else:
            print(f"FAIL: {name} status {resp.status_code}")
            print(resp.text[:200])
    except Exception as e:
        print(f"ERROR: {name} - {e}")

test_route("News API", "http://127.0.0.1:5001/api/news")
test_route("Portfolio API", "http://127.0.0.1:5001/api/portfolio")
