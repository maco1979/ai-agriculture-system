#!/usr/bin/env python3
"""
区块链溯源管理脚本 - OpenClaw技能辅助工具
用法:
  python blockchain.py status
  python blockchain.py register-model --model-id organic_core --version 1.0.0
  python blockchain.py verify-model   --model-id organic_core --hash abc123
  python blockchain.py model-history  --model-id organic_core
  python blockchain.py record-provenance --data-id dataset_001 --model-id organic_core --operation training
  python blockchain.py get-provenance --data-id dataset_001
  python blockchain.py access-rights
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
        body_text = ""
        try:
            body_text = e.read().decode()
        except Exception:
            pass
        return {"error": f"HTTP {e.code}", "detail": body_text}
    except Exception as e:
        return {"error": str(e)}


def ok(r):
    return "error" not in r


def sep(title=""):
    print(f"\n{'━'*50}")
    if title:
        print(f"  🔗 {title}")
        print("━" * 50)


def cmd_status(args):
    result = get_json("/api/blockchain/status")
    sep("区块链网络状态")
    if "error" in result:
        print(f"  ❌ {result['error']}")
        print("  💡 Hyperledger Fabric 节点未运行 → 系统使用模拟模式")
        sys.exit(1)

    data = result.get("data", result)
    network_status = data.get("status", "unknown")
    initialized = data.get("initialized", False)
    block = data.get("latest_block", {})
    ts = data.get("timestamp", "")[:19]

    icon = "✅" if network_status == "running" else "⚠️"
    print(f"  {icon} 网络状态  : {network_status}")
    print(f"  🔧 已初始化  : {'是' if initialized else '否'}")
    if block:
        print(f"  📦 最新区块  : #{block.get('block_number', 'N/A')}")
        print(f"  📝 交易数量  : {block.get('transaction_count', 'N/A')}")
    print(f"  🕐 查询时间  : {ts}")

    success = result.get("success", True)
    if not success:
        print("\n  ⚠️  当前为模拟模式，区块数据为仿真数据")
    print()


def cmd_register_model(args):
    data = {
        "model_id": args.model_id,
        "model_bytes": f"model_{args.version}_{datetime.now().isoformat()}",
        "metadata": {
            "version": args.version,
            "description": args.description,
            "registered_at": datetime.now().isoformat()
        }
    }
    result = post_json("/api/blockchain/models/register", data)
    sep(f"注册模型到区块链: {args.model_id}")
    if ok(result):
        tx_id = result.get("transaction_id", result.get("txId", "N/A"))
        model_hash = result.get("model_hash", result.get("hash", "N/A"))
        print(f"  ✅ 注册成功")
        print(f"  📋 模型ID    : {args.model_id}")
        print(f"  🔖 版本      : {args.version}")
        print(f"  🔐 模型哈希  : {model_hash}")
        print(f"  📝 交易ID    : {tx_id}")
    else:
        print(f"  ❌ 注册失败: {result['error']}")
        detail = result.get("detail", "")
        if "503" in str(result.get("error")):
            print("  💡 区块链功能不可用（需要Hyperledger Fabric节点）")
        elif detail:
            print(f"     详情: {detail}")
    print()


def cmd_verify_model(args):
    data = {"model_hash": args.hash}
    result = post_json(f"/api/blockchain/models/{args.model_id}/verify", data)
    sep(f"验证模型完整性: {args.model_id}")
    if ok(result):
        verified = result.get("verified", result.get("is_valid", False))
        icon = "✅" if verified else "❌"
        print(f"  {icon} 完整性验证: {'通过' if verified else '失败'}")
        if not verified:
            print("  ⚠️  模型哈希不匹配，可能已被篡改！")
        stored_hash = result.get("stored_hash", "N/A")
        print(f"  🔐 存储哈希  : {stored_hash}")
        print(f"  🔐 提交哈希  : {args.hash}")
    else:
        print(f"  ❌ 验证失败: {result['error']}")
    print()


def cmd_model_history(args):
    result = get_json(f"/api/blockchain/models/{args.model_id}/history")
    sep(f"模型版本历史: {args.model_id}")
    if ok(result):
        history = result.get("history", result.get("data", []))
        if isinstance(history, list) and history:
            print(f"  📜 共 {len(history)} 个版本记录\n")
            for i, entry in enumerate(history, 1):
                ver = entry.get("version", "N/A")
                ts = str(entry.get("timestamp", entry.get("created_at", "")))[:19]
                tx = entry.get("transaction_id", entry.get("txId", ""))[:16]
                print(f"  {i:2}. v{ver}  [{ts}]  tx:{tx}...")
        else:
            print("  （暂无版本记录）")
    else:
        print(f"  ❌ 获取历史失败: {result['error']}")
    print()


def cmd_record_provenance(args):
    data = {
        "data_id": args.data_id,
        "model_id": args.model_id,
        "operation": args.operation,
        "metadata": {
            "recorded_at": datetime.now().isoformat(),
            "operator": "openclaw-agent"
        }
    }
    result = post_json("/api/blockchain/data/provenance", data)
    op_cn = {"training": "训练数据使用", "inference": "推理数据使用"}
    sep(f"记录数据溯源: {args.data_id}")
    if ok(result):
        tx_id = result.get("transaction_id", result.get("txId", "N/A"))
        print(f"  ✅ 溯源记录成功")
        print(f"  📦 数据ID    : {args.data_id}")
        print(f"  🤖 关联模型  : {args.model_id}")
        print(f"  🔧 操作类型  : {op_cn.get(args.operation, args.operation)}")
        print(f"  📝 交易ID    : {tx_id}")
    else:
        print(f"  ❌ 记录失败: {result['error']}")
    print()


def cmd_get_provenance(args):
    result = get_json(f"/api/blockchain/data/{args.data_id}/provenance")
    sep(f"数据溯源查询: {args.data_id}")
    if ok(result):
        records = result.get("provenance", result.get("data", []))
        if isinstance(records, list) and records:
            print(f"  📜 共 {len(records)} 条溯源记录\n")
            for i, r in enumerate(records, 1):
                op = r.get("operation", "N/A")
                model = r.get("model_id", "N/A")
                ts = str(r.get("timestamp", r.get("created_at", "")))[:19]
                print(f"  {i:2}. [{ts}]  操作:{op}  模型:{model}")
        else:
            print("  （该数据暂无溯源记录）")
    else:
        print(f"  ❌ 查询失败: {result['error']}")
    print()


def cmd_access_rights(args):
    result = get_json("/api/blockchain/access-rights")
    sep("访问权限列表")
    if ok(result):
        rights = result if isinstance(result, list) else result.get("access_rights", result.get("data", []))
        if isinstance(rights, list) and rights:
            print(f"  共 {len(rights)} 条权限记录\n")
            for r in rights:
                user = r.get("user_id", r.get("user", "N/A"))
                res = r.get("resource", "N/A")
                perm = r.get("permission", "N/A")
                print(f"  👤 {user:<20} → {res:<20} [{perm}]")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"  ❌ 获取权限列表失败: {result['error']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="区块链溯源管理工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="查看区块链网络状态")
    sub.add_parser("access-rights", help="查看访问权限列表")

    p_reg = sub.add_parser("register-model", help="注册模型到区块链")
    p_reg.add_argument("--model-id", required=True, dest="model_id")
    p_reg.add_argument("--version", default="1.0.0")
    p_reg.add_argument("--description", default="", help="模型描述")

    p_ver = sub.add_parser("verify-model", help="验证模型完整性")
    p_ver.add_argument("--model-id", required=True, dest="model_id")
    p_ver.add_argument("--hash", required=True, help="模型哈希值")

    p_hist = sub.add_parser("model-history", help="查看模型版本历史")
    p_hist.add_argument("--model-id", required=True, dest="model_id")

    p_rec = sub.add_parser("record-provenance", help="记录数据溯源")
    p_rec.add_argument("--data-id", required=True, dest="data_id")
    p_rec.add_argument("--model-id", required=True, dest="model_id")
    p_rec.add_argument("--operation", default="training",
                       choices=["training", "inference"])

    p_get = sub.add_parser("get-provenance", help="查询数据溯源")
    p_get.add_argument("--data-id", required=True, dest="data_id")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "status": cmd_status,
        "register-model": cmd_register_model,
        "verify-model": cmd_verify_model,
        "model-history": cmd_model_history,
        "record-provenance": cmd_record_provenance,
        "get-provenance": cmd_get_provenance,
        "access-rights": cmd_access_rights,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
