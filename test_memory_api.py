import urllib.request
import json

def api_call(url, method='GET', data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.data = json.dumps(data).encode()
            req.add_header('Content-Type', 'application/json')
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

print("=== 智能体记忆API测试 ===\n")

# 1. 查看初始记忆状态
print("1. 初始记忆状态:")
mem = api_call('http://localhost:8001/api/v1/fine-tune/memory')
print(f"   总记忆数: {mem.get('data', {}).get('total_memories', 0)}")

# 2. 模拟添加记忆
print("\n2. 模拟添加5条记忆:")
add_result = api_call('http://localhost:8001/api/v1/fine-tune/memory/simulate?count=5', 'POST')
print(f"   添加成功: {add_result.get('success')}")
print(f"   添加数量: {add_result.get('data', {}).get('added_count', 0)}")
print(f"   当前总记忆: {add_result.get('data', {}).get('total_memories', 0)}")

# 3. 查看记忆详情
print("\n3. 查看记忆详情:")
mem = api_call('http://localhost:8001/api/v1/fine-tune/memory?limit=3')
memories = mem.get('data', {}).get('memories', [])
for i, m in enumerate(memories):
    print(f"   [{i+1}] {m.get('memory_id')}: {m.get('experience', {}).get('action')} -> reward={m.get('reward'):.2f}")

# 4. 查看OrganicAICore状态
print("\n4. OrganicAICore状态:")
status = api_call('http://localhost:8001/api/v1/fine-tune/status')
data = status.get('data', {})
print(f"   学习记忆大小: {data.get('learning_memory_size')}")
print(f"   成功率: {data.get('performance_metrics', {}).get('success_rate')}")
print(f"   平均奖励: {data.get('performance_metrics', {}).get('average_reward')}")

print("\n=== 测试完成 ===")
