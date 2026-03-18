import urllib.request
import json

def test_training():
    # 1. 创建训练任务
    req = urllib.request.Request(
        'http://localhost:8001/api/models/organic_core_v1/train',
        data=json.dumps({"epochs": 10}).encode(),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    r = urllib.request.urlopen(req, timeout=5)
    data = json.loads(r.read())
    print("Create training task:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    task_id = data['data']['task_id']
    
    # 2. 查询训练状态
    r = urllib.request.urlopen(f'http://localhost:8001/api/models/training/{task_id}', timeout=5)
    status = json.loads(r.read())
    print("\nTraining status:")
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # 3. 测试旧任务ID（模拟重启后查询）
    r = urllib.request.urlopen('http://localhost:8001/api/models/training/task_old_12345', timeout=5)
    old_status = json.loads(r.read())
    print("\nOld task status (should return completed):")
    print(json.dumps(old_status, indent=2, ensure_ascii=False))

test_training()
