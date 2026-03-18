import urllib.request
import json

def test_api(url, method='GET', data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.data = json.dumps(data).encode()
            req.add_header('Content-Type', 'application/json')
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

print("=== 智能体记忆测试 ===\n")

# 1. 获取 OrganicAICore 状态（包含学习记忆大小）
print("1. OrganicAICore 状态:")
status = test_api('http://localhost:8001/api/v1/fine-tune/status')
print(json.dumps(status, indent=2, ensure_ascii=False)[:1500])

# 2. 获取AI控制设备
print("\n2. AI控制设备列表:")
devices = test_api('http://localhost:8001/api/ai-control/devices')
print(json.dumps(devices, indent=2, ensure_ascii=False)[:500])

# 3. 获取主控制状态
print("\n3. 主控制状态:")
master = test_api('http://localhost:8001/api/ai-control/master-control/status')
print(json.dumps(master, indent=2, ensure_ascii=False))

print("\n=== 测试完成 ===")
