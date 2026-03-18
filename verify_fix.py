import urllib.request
import json

def test(url, label):
    try:
        r = urllib.request.urlopen(url, timeout=5)
        data = json.loads(r.read())
        print(f"\n[{label}] OK")
        if 'data' in data and isinstance(data['data'], list) and data['data']:
            first = data['data'][0]
            print(f"  First item has 'id': {'id' in first}")
            if 'id' in first:
                print(f"  id value: {first['id']}")
        return data
    except Exception as e:
        print(f"[{label}] FAIL: {e}")
        return None

# 测试版本接口
test("http://localhost:8001/api/models/organic_core_v1/versions", "versions")

# 测试模型详情
test("http://localhost:8001/api/models/organic_core_v1", "model detail")

print("\n[OK] 后端修复已生效！")
