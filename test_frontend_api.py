import urllib.request
import json

# 模拟前端调用 /api/models 并检查数据结构
try:
    r = urllib.request.urlopen('http://localhost:8001/api/models', timeout=5)
    data = json.loads(r.read())
    
    print("Response structure:")
    print("  - success:", data.get('success'))
    print("  - data type:", type(data.get('data')))
    print("  - data length:", len(data.get('data', [])))
    
    # 检查第一个模型的字段
    if data.get('data'):
        first = data['data'][0]
        print("\nFirst model fields:")
        for key in first:
            print(f"  - {key}: {type(first[key]).__name__} = {repr(first[key])[:60]}")
            
except Exception as e:
    print('Error:', e)
