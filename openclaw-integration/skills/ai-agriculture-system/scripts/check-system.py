#!/usr/bin/env python3
"""
AI农业决策系统 - 系统状态检查脚本
OpenClaw 技能辅助脚本
用法: python check-system.py [--json]
"""
import urllib.request
import json
import sys
import argparse

BASE_URL = "http://localhost:8001"

def fetch(path, timeout=5):
    try:
        url = f"{BASE_URL}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="输出原始JSON")
    args = parser.parse_args()

    results = {}

    # 健康检查
    health = fetch("/api/system/health")
    results["health"] = health

    # 系统指标
    metrics = fetch("/api/system/metrics")
    results["metrics"] = metrics

    # 模型列表
    models = fetch("/api/models")
    results["models"] = models

    # 边缘设备
    edge = fetch("/api/edge/devices")
    results["edge_devices"] = edge

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    # 友好输出
    print("=" * 50)
    print("🌾 AI农业决策系统 — 状态报告")
    print("=" * 50)

    if "error" in health:
        print(f"❌ 服务离线: {health['error']}")
        print("   请运行: cd d:/1.6/1.5/backend && python simple_api.py")
        sys.exit(1)
    else:
        status = health.get("status", "unknown")
        emoji = "✅" if status == "healthy" else "⚠️"
        print(f"{emoji} 服务状态: {status}")

    if "error" not in metrics:
        cpu = metrics.get("cpu_percent", "N/A")
        mem = metrics.get("memory_percent", "N/A")
        disk = metrics.get("disk_percent", "N/A")
        print(f"📊 CPU: {cpu}%  |  内存: {mem}%  |  磁盘: {disk}%")

    if "error" not in models and isinstance(models, list):
        print(f"\n🤖 已注册AI模型: {len(models)} 个")
        for m in models[:5]:
            name = m.get("name", m.get("id", "未知"))
            mtype = m.get("model_type", "")
            mstatus = m.get("status", "")
            print(f"   • {name} [{mtype}] — {mstatus}")
        if len(models) > 5:
            print(f"   ... 还有 {len(models)-5} 个模型")

    if "error" not in edge and isinstance(edge, list):
        print(f"\n🌐 边缘设备: {len(edge)} 个在线")

    print("\n🔗 API文档: http://localhost:8001/docs")
    print("=" * 50)

if __name__ == "__main__":
    main()
