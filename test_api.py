import urllib.request
import json

def test(url, label=""):
    try:
        r = urllib.request.urlopen(url, timeout=5)
        data = json.loads(r.read())
        print(f"[{label or url}] OK: {json.dumps(data, ensure_ascii=False)[:300]}")
    except Exception as e:
        print(f"[{label or url}] FAIL: {e}")

test("http://localhost:8001/api/models/organic_core_v1", "detail")
test("http://localhost:8001/api/models/organic_core_v1/versions", "versions")
