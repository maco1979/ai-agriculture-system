import urllib.request
import json
import sys

def api_call(endpoint, method='GET', data=None):
    """调用API"""
    try:
        url = f'http://localhost:8001{endpoint}'
        req = urllib.request.Request(url, method=method)
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {'error': str(e)}

print("=" * 60)
print("AI农业项目API能力分析")
print("=" * 60)

apis = [
    ('GET', '/api/models', '模型列表'),
    ('GET', '/api/agriculture/crop-configs', '作物配置'),
    ('GET', '/api/community/live-streams', '社区直播'),
    ('GET', '/api/system/metrics', '系统指标'),
    ('GET', '/api/edge/devices', '边缘设备'),
    ('GET', '/api/blockchain/status', '区块链状态'),
    ('GET', '/api/federated/status', '联邦学习状态'),
    ('GET', '/api/ai-control/devices', 'AI控制设备'),
    ('GET', '/api/v1/fine-tune/status', '智能体状态'),
]

for method, endpoint, name in apis:
    result = api_call(endpoint, method)
    if isinstance(result, dict):
        status = 'OK' if result.get('success') else 'FAIL'
        print(f"[{status}] {name}: {endpoint}")
        if result.get('data'):
            if isinstance(result['data'], list):
                print(f"       返回 {len(result['data'])} 条数据")
            elif isinstance(result['data'], dict):
                print(f"       字段: {', '.join(list(result['data'].keys())[:5])}")
    else:
        print(f"[ERROR] {name}: {endpoint} - 返回类型错误")

print("\n" + "=" * 60)
