#!/usr/bin/env python3
"""
AI农业智能决策系统 CLI 控制器
用于 WorkBuddy 技能调用
"""

import urllib.request
import urllib.error
import json
import sys
import argparse
from datetime import datetime

BASE_URL = "http://localhost:8001"


def api_call(endpoint, method='GET', data=None):
    """调用API"""
    try:
        url = f"{BASE_URL}{endpoint}"
        req = urllib.request.Request(url, method=method)
        if data:
            req.data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'success': False, 'error': f'HTTP {e.code}: {e.reason}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_health():
    """检查服务健康状态"""
    result = api_call('/health')
    if result.get('status') == 'healthy':
        print("[OK] AI农业系统运行正常")
        print(f"     版本: {result.get('version', 'unknown')}")
        print(f"     时间: {result.get('timestamp', 'unknown')}")
        return True
    else:
        print("[ERROR] AI农业系统未运行")
        print(f"       错误: {result.get('error', 'unknown')}")
        return False


def get_system_status():
    """获取系统整体状态"""
    print("=" * 60)
    print("AI农业智能决策系统 - 整体状态")
    print("=" * 60)
    
    # 健康检查
    health = api_call('/health')
    if health.get('status') != 'healthy':
        print("[ERROR] 服务未运行，请先启动后端服务")
        return
    
    print(f"[OK] 服务运行正常 (版本: {health.get('version')})")
    print()
    
    # 系统指标
    metrics = api_call('/api/system/metrics')
    if metrics.get('success'):
        data = metrics['data']
        print("[系统资源]")
        print(f"  CPU使用率: {data.get('cpu_usage', 0)}%")
        print(f"  内存使用率: {data.get('memory_usage', 0)}%")
        print(f"  磁盘使用率: {data.get('disk_usage', 0)}%")
        print(f"  活跃连接: {data.get('active_connections', 0)}")
        print(f"  运行时间: {data.get('uptime', 'unknown')}")
        print()
    
    # AI模型
    models = api_call('/api/models')
    if models.get('success') and models.get('data'):
        model_list = models['data']
        running = sum(1 for m in model_list if m.get('status') in ['ready', 'deployed'])
        training = sum(1 for m in model_list if m.get('status') == 'training')
        print(f"[AI模型] 共{len(model_list)}个模型")
        print(f"  运行中: {running}个")
        print(f"  训练中: {training}个")
        print()
    
    # 智能体状态
    agent = api_call('/api/v1/fine-tune/status')
    if agent.get('success'):
        data = agent['data']
        print("[智能体状态]")
        print(f"  状态: {data.get('state', 'unknown')}")
        print(f"  学习记忆: {data.get('learning_memory_size', 0)}条")
        print(f"  决策次数: {data.get('decision_count', 0)}")
        metrics = data.get('performance_metrics', {})
        print(f"  成功率: {metrics.get('success_rate', 0)*100:.1f}%")
        print()
    
    # 区块链状态
    blockchain = api_call('/api/blockchain/status')
    if blockchain.get('success'):
        data = blockchain['data']
        print("[区块链]")
        print(f"  状态: {data.get('status', 'unknown')}")
        print(f"  已连接: {'是' if data.get('connected') else '否'}")
        print(f"  节点数: {data.get('peers', 0)}")
        print(f"  最新区块: {data.get('latest_block', 0)}")
        print()
    
    # 联邦学习
    federated = api_call('/api/federated/status')
    if federated.get('success'):
        data = federated['data']
        print("[联邦学习]")
        print(f"  状态: {data.get('status', 'unknown')}")
        print(f"  当前轮次: {data.get('current_round', 0)}")
        print(f"  总客户端: {data.get('total_clients', 0)}")
        print(f"  活跃客户端: {data.get('active_clients', 0)}")
        print()
    
    print("=" * 60)


def list_models():
    """列出所有AI模型"""
    print("=" * 60)
    print("AI模型列表")
    print("=" * 60)
    
    result = api_call('/api/models')
    if not result.get('success'):
        print(f"[ERROR] 获取失败: {result.get('error')}")
        return
    
    models = result.get('data', [])
    print(f"共 {len(models)} 个模型:\n")
    
    for i, model in enumerate(models, 1):
        status = model.get('status', 'unknown')
        status_icon = {
            'ready': '[运行中]',
            'deployed': '[运行中]',
            'training': '[训练中]',
            'error': '[错误]'
        }.get(status, f'[{status}]')
        
        print(f"{i}. {status_icon} {model.get('name', 'Unknown')}")
        print(f"   ID: {model.get('id')}")
        print(f"   类型: {model.get('type', 'unknown')}")
        print(f"   准确率: {model.get('accuracy', 0)*100:.1f}%")
        print(f"   框架: {model.get('framework', 'unknown')}")
        print()


def get_model_detail(model_id):
    """获取模型详情"""
    print("=" * 60)
    print(f"模型详情: {model_id}")
    print("=" * 60)
    
    result = api_call(f'/api/models/{model_id}')
    if not result.get('success'):
        print(f"[ERROR] 获取失败: {result.get('error')}")
        return
    
    model = result.get('data', {})
    print(f"名称: {model.get('name')}")
    print(f"ID: {model.get('id')}")
    print(f"类型: {model.get('type')}")
    print(f"状态: {model.get('status')}")
    print(f"版本: {model.get('version')}")
    print(f"准确率: {model.get('accuracy', 0)*100:.1f}%")
    print(f"框架: {model.get('framework')}")
    print(f"推荐模型: {model.get('recommended_model')}")
    print(f"任务: {model.get('task')}")
    print()
    print(f"描述: {model.get('description', '无')[:200]}...")


def train_model(model_id):
    """启动模型训练"""
    print(f"启动模型训练: {model_id}")
    
    result = api_call(f'/api/models/{model_id}/train', 'POST', {
        'epochs': 10,
        'batch_size': 32
    })
    
    if result.get('success'):
        data = result.get('data', {})
        print(f"[OK] 训练任务已启动")
        print(f"     任务ID: {data.get('task_id')}")
        print(f"     消息: {data.get('message')}")
    else:
        print(f"[ERROR] 启动失败: {result.get('error')}")


def get_agriculture_config():
    """获取农业决策配置"""
    print("=" * 60)
    print("农业决策配置")
    print("=" * 60)
    
    result = api_call('/api/agriculture/crop-configs')
    if not result.get('success'):
        print(f"[ERROR] 获取失败: {result.get('error')}")
        return
    
    configs = result.get('data', {})
    for crop_name, config in configs.items():
        print(f"\n[{crop_name}]")
        print(f"  光配方: {config.get('light_recipe', 'N/A')}")
        print(f"  温度: {config.get('temperature', 'N/A')}°C")
        print(f"  湿度: {config.get('humidity', 'N/A')}%")
        print(f"  CO2: {config.get('co2', 'N/A')} ppm")


def get_memory():
    """查看智能体记忆"""
    print("=" * 60)
    print("智能体学习记忆")
    print("=" * 60)
    
    result = api_call('/api/v1/fine-tune/memory')
    if not result.get('success'):
        print(f"[ERROR] 获取失败: {result.get('error')}")
        return
    
    data = result.get('data', {})
    total = data.get('total_memories', 0)
    memories = data.get('memories', [])
    
    print(f"总记忆数: {total}")
    print(f"显示最近 {len(memories)} 条:\n")
    
    for i, mem in enumerate(memories, 1):
        print(f"{i}. [{mem.get('memory_id')}]")
        print(f"   经验: {mem.get('experience', {})}")
        print(f"   奖励: {mem.get('reward', 0):.2f}")
        print(f"   成功: {'是' if mem.get('success') else '否'}")
        print(f"   时间: {mem.get('timestamp', 'unknown')}")
        print()


def add_memory():
    """模拟添加记忆"""
    print("模拟添加学习记忆...")
    
    result = api_call('/api/v1/fine-tune/memory/simulate?count=3', 'POST')
    if result.get('success'):
        data = result.get('data', {})
        print(f"[OK] 成功添加 {data.get('added_count', 0)} 条记忆")
        print(f"     当前总记忆: {data.get('total_memories', 0)}")
    else:
        print(f"[ERROR] 添加失败: {result.get('error')}")


def get_monitor():
    """查看系统监控"""
    print("=" * 60)
    print("系统监控")
    print("=" * 60)
    
    # 系统指标
    metrics = api_call('/api/system/metrics')
    if metrics.get('success'):
        data = metrics['data']
        print("\n[资源使用]")
        print(f"  CPU: {data.get('cpu_usage', 0)}%")
        print(f"  内存: {data.get('memory_usage', 0)}%")
        print(f"  磁盘: {data.get('disk_usage', 0)}%")
        print(f"  网络入: {data.get('network_in', 0)} KB/s")
        print(f"  网络出: {data.get('network_out', 0)} KB/s")
    
    # 边缘设备
    devices = api_call('/api/edge/devices')
    if devices.get('success'):
        device_list = devices.get('data', [])
        print(f"\n[边缘设备] 共{len(device_list)}个")
        for d in device_list:
            status = '在线' if d.get('status') == 'online' else '离线'
            print(f"  - {d.get('name')} ({status})")


def camera_control(action):
    """摄像头控制"""
    if action == 'open':
        result = api_call('/api/camera/open', 'POST')
        if result.get('success'):
            print("[OK] 摄像头已打开")
        else:
            print(f"[ERROR] {result.get('error')}")
    
    elif action == 'close':
        result = api_call('/api/camera/close', 'POST')
        if result.get('success'):
            print("[OK] 摄像头已关闭")
        else:
            print(f"[ERROR] {result.get('error')}")
    
    elif action == 'frame':
        result = api_call('/api/camera/frame')
        if result.get('success'):
            print("[OK] 获取图像帧成功")
            print(f"     格式: {result.get('data', {}).get('format', 'unknown')}")
        else:
            print(f"[ERROR] {result.get('error')}")


def ptz_control(direction):
    """PTZ云台控制"""
    direction_map = {
        'up': (0, 10),
        'down': (0, -10),
        'left': (-10, 0),
        'right': (10, 0)
    }
    
    if direction not in direction_map:
        print(f"[ERROR] 未知方向: {direction}")
        return
    
    pan, tilt = direction_map[direction]
    result = api_call('/api/camera/ptz/move', 'POST', {
        'pan': pan,
        'tilt': tilt
    })
    
    if result.get('success'):
        print(f"[OK] PTZ云台已向{direction}移动")
    else:
        print(f"[ERROR] {result.get('error')}")


def main():
    parser = argparse.ArgumentParser(description='AI农业智能决策系统 CLI')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # status
    subparsers.add_parser('status', help='查看系统整体状态')
    
    # models
    subparsers.add_parser('models', help='列出所有AI模型')
    
    # model
    model_parser = subparsers.add_parser('model', help='查看模型详情')
    model_parser.add_argument('model_id', help='模型ID')
    
    # train
    train_parser = subparsers.add_parser('train', help='启动模型训练')
    train_parser.add_argument('model_id', help='模型ID')
    
    # agriculture
    subparsers.add_parser('agriculture', help='查看农业决策配置')
    
    # memory
    subparsers.add_parser('memory', help='查看智能体记忆')
    
    # memory-add
    subparsers.add_parser('memory-add', help='模拟添加记忆')
    
    # monitor
    subparsers.add_parser('monitor', help='查看系统监控')
    
    # camera
    camera_parser = subparsers.add_parser('camera', help='摄像头控制')
    camera_parser.add_argument('action', choices=['open', 'close', 'frame'])
    
    # ptz
    ptz_parser = subparsers.add_parser('ptz', help='PTZ云台控制')
    ptz_parser.add_argument('direction', choices=['up', 'down', 'left', 'right'])
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == 'status':
        get_system_status()
    elif args.command == 'models':
        list_models()
    elif args.command == 'model':
        get_model_detail(args.model_id)
    elif args.command == 'train':
        train_model(args.model_id)
    elif args.command == 'agriculture':
        get_agriculture_config()
    elif args.command == 'memory':
        get_memory()
    elif args.command == 'memory-add':
        add_memory()
    elif args.command == 'monitor':
        get_monitor()
    elif args.command == 'camera':
        camera_control(args.action)
    elif args.command == 'ptz':
        ptz_control(args.direction)


if __name__ == '__main__':
    main()
