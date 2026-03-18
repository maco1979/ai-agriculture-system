#!/usr/bin/env python3
"""
联邦学习管理脚本 - OpenClaw技能辅助工具
用法:
  python federated.py clients
  python federated.py register  --client-id node_001 --data-size 5000 --privacy-budget 1.0
  python federated.py start-round --model-id organic_core --min-clients 2 --rounds 5
  python federated.py submit-update --round-id round_001 --client-id node_001
  python federated.py aggregate   --round-id round_001
  python federated.py status
"""
import urllib.request
import urllib.error
import json
import sys
import argparse
from datetime import datetime

BASE_URL = "http://localhost:8001"


def get_json(path, timeout=10):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        return {"error": f"连接失败: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def post_json(path, data, timeout=15):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode()
        except Exception:
            pass
        return {"error": f"HTTP {e.code}", "detail": detail}
    except Exception as e:
        return {"error": str(e)}


def ok(r):
    return "error" not in r


def sep(title=""):
    print(f"\n{'━'*50}")
    if title:
        print(f"  🌐 {title}")
        print("━" * 50)


def cmd_clients(args):
    result = get_json("/api/federated/clients")
    sep("联邦学习客户端列表")
    if "error" in result:
        print(f"  ❌ {result['error']}")
        sys.exit(1)

    data = result.get("data", result if isinstance(result, list) else [])
    total = result.get("total_count", len(data))
    print(f"  已注册客户端: {total} 个\n")

    if isinstance(data, list) and data:
        print(f"  {'客户端ID':<25} {'数据量':<12} {'状态'}")
        print(f"  {'─'*55}")
        for c in data:
            cid = c.get("client_id", c.get("id", "N/A"))
            dsize = c.get("data_size", c.get("dataset_size", "N/A"))
            status = c.get("status", c.get("state", "registered"))
            print(f"  {cid:<25} {str(dsize):<12} {status}")
    else:
        print("  （暂无已注册客户端）")
        print("  💡 提示: 至少需要2个客户端才能开始联邦训练")
    print()


def cmd_register(args):
    data = {
        "client_id": args.client_id,
        "data_size": args.data_size,
        "privacy_budget": args.privacy_budget,
        "registered_at": datetime.now().isoformat(),
        "capabilities": {
            "gpu": False,
            "cpu_cores": 4,
            "memory_gb": 8
        }
    }
    result = post_json("/api/federated/clients/register", data)
    sep(f"注册联邦客户端: {args.client_id}")
    if ok(result):
        print(f"  ✅ 注册成功")
        print(f"  🆔 客户端ID  : {args.client_id}")
        print(f"  📦 数据量    : {args.data_size} 条")
        print(f"  🔒 隐私预算  : ε={args.privacy_budget}")
    else:
        print(f"  ❌ 注册失败: {result['error']}")
        detail = result.get("detail", "")
        if "已存在" in detail or "400" in str(result.get("error", "")):
            print(f"  💡 客户端 {args.client_id} 已注册过")
    print()


def cmd_start_round(args):
    data = {
        "model_id": args.model_id,
        "min_clients": args.min_clients,
        "num_rounds": args.rounds,
        "started_at": datetime.now().isoformat(),
        "aggregation_strategy": "fedavg"
    }
    result = post_json("/api/federated/rounds/start", data)
    sep("开始联邦训练轮次")
    if ok(result):
        round_info = result.get("round_info", result)
        round_id = round_info.get("round_id", round_info.get("id", "N/A"))
        print(f"  ✅ 训练轮次已开始")
        print(f"  🔖 轮次ID    : {round_id}")
        print(f"  🤖 目标模型  : {args.model_id}")
        print(f"  👥 最少客户端: {args.min_clients}")
        print(f"  🔄 轮次数    : {args.rounds}")
        print(f"\n  📌 记录此轮次ID，提交更新时需要用到: {round_id}")
    else:
        print(f"  ❌ 启动失败: {result['error']}")
        detail = result.get("detail", "")
        if detail:
            print(f"     详情: {detail}")
    print()


def cmd_submit_update(args):
    # 模拟模型更新权重（实际应由客户端本地训练产生）
    data = {
        "client_id": args.client_id,
        "model_bytes": f"model_update_{args.client_id}_{datetime.now().isoformat()}",
        "metrics": {
            "loss": 0.245,
            "accuracy": 0.912,
            "data_size": 1000,
            "local_epochs": 5
        }
    }
    result = post_json(f"/api/federated/rounds/{args.round_id}/updates", data)
    sep(f"提交模型更新: 轮次 {args.round_id}")
    if ok(result):
        print(f"  ✅ 更新提交成功")
        print(f"  🆔 客户端    : {args.client_id}")
        print(f"  📊 本地损失  : 0.245")
        print(f"  📊 本地精度  : 91.2%")
    else:
        print(f"  ❌ 提交失败: {result['error']}")
    print()


def cmd_aggregate(args):
    data = {"aggregation_strategy": "fedavg"}
    # 尝试聚合端点（不同版本路由略有差异）
    result = post_json(f"/api/federated/rounds/{args.round_id}/aggregate", data)
    if "error" in result and "404" in str(result.get("error", "")):
        # 回退到 complete 端点
        result = post_json(f"/api/federated/rounds/{args.round_id}/complete", {
            "metrics": {"aggregated": True},
            "model_bytes": "aggregated_model_placeholder"
        })
    sep(f"聚合联邦模型: 轮次 {args.round_id}")
    if ok(result):
        print(f"  ✅ 聚合完成")
        metrics = result.get("metrics", result.get("aggregated_metrics", {}))
        if metrics:
            loss = metrics.get("loss", metrics.get("avg_loss", "N/A"))
            acc = metrics.get("accuracy", metrics.get("avg_accuracy", "N/A"))
            participants = metrics.get("participants", metrics.get("num_clients", "N/A"))
            print(f"  📊 聚合损失  : {loss}")
            print(f"  📊 聚合精度  : {acc}")
            print(f"  👥 参与客户端: {participants}")
        model_hash = result.get("model_hash", result.get("aggregated_model_hash", ""))
        if model_hash:
            print(f"  🔐 聚合模型哈希: {model_hash[:32]}...")
    else:
        print(f"  ❌ 聚合失败: {result['error']}")
    print()


def cmd_status(args):
    sep("联邦学习全局状态")

    # 客户端数量
    clients = get_json("/api/federated/clients")
    if ok(clients):
        total = clients.get("total_count", len(clients.get("data", [])))
        print(f"  👥 已注册客户端: {total} 个")
        min_needed = 2
        ready = "✅ 可以开始训练" if total >= min_needed else f"⚠️  还需至少 {min_needed - total} 个客户端"
        print(f"     状态: {ready}")
    else:
        print(f"  ❌ 无法获取客户端状态: {clients['error']}")

    # 当前轮次
    current = get_json("/api/federated/rounds/current")
    if ok(current) and current:
        rid = current.get("round_id", current.get("id", "N/A"))
        rstatus = current.get("status", current.get("state", "N/A"))
        print(f"\n  🔄 当前轮次: {rid}  [{rstatus}]")
    else:
        print(f"\n  🔄 当前无活跃训练轮次")

    print()


def main():
    parser = argparse.ArgumentParser(description="联邦学习管理工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("clients", help="列出所有联邦客户端")
    sub.add_parser("status", help="查看联邦学习全局状态")

    p_reg = sub.add_parser("register", help="注册新客户端")
    p_reg.add_argument("--client-id", required=True, dest="client_id")
    p_reg.add_argument("--data-size", type=int, default=1000, dest="data_size")
    p_reg.add_argument("--privacy-budget", type=float, default=1.0, dest="privacy_budget",
                       help="差分隐私预算 ε（越小越严格）")

    p_start = sub.add_parser("start-round", help="开始训练轮次")
    p_start.add_argument("--model-id", required=True, dest="model_id")
    p_start.add_argument("--min-clients", type=int, default=2, dest="min_clients")
    p_start.add_argument("--rounds", type=int, default=5)

    p_sub = sub.add_parser("submit-update", help="提交客户端模型更新")
    p_sub.add_argument("--round-id", required=True, dest="round_id")
    p_sub.add_argument("--client-id", required=True, dest="client_id")

    p_agg = sub.add_parser("aggregate", help="聚合本轮模型")
    p_agg.add_argument("--round-id", required=True, dest="round_id")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "clients": cmd_clients,
        "register": cmd_register,
        "start-round": cmd_start_round,
        "submit-update": cmd_submit_update,
        "aggregate": cmd_aggregate,
        "status": cmd_status,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
