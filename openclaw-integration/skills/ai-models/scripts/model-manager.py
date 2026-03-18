#!/usr/bin/env python3
"""
AI模型管理脚本 - OpenClaw技能辅助工具
用法:
  python model-manager.py list
  python model-manager.py info --model organic_core
  python model-manager.py start --model organic_core
  python model-manager.py pause --model risk_model
  python model-manager.py train --model vision_model --epochs 10 --lr 0.001
  python model-manager.py infer --model risk_model --input '{"crop_type":"番茄"}'
  python model-manager.py history --limit 10
"""
import urllib.request
import urllib.error
import json
import sys
import argparse

BASE_URL = "http://localhost:8001"

STATUS_MAP = {
    "running": "✅ 运行中",
    "paused": "⏸ 已暂停",
    "training": "🏋️ 训练中",
    "idle": "💤 空闲",
    "error": "❌ 错误",
    "stopped": "⏹ 已停止",
}

MODEL_CN = {
    "organic_core": "OrganicCore(PPO强化学习)",
    "advanced_core": "PatchTST(时序Transformer)",
    "vision_model": "ResNet50(视觉分类)",
    "meta_learning": "MAML(元学习)",
    "curiosity_model": "ICM(好奇心探索)",
    "risk_model": "LightGBM(风险评估)",
    "timeseries": "TimesNet(时序预测)",
}

def post_json(path, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data or {}, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "detail": e.read().decode()}
    except Exception as e:
        return {"error": str(e)}

def get_json(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def ok(r):
    return "error" not in r

def main():
    parser = argparse.ArgumentParser(description="AI模型管理工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有模型")

    p_info = sub.add_parser("info", help="模型详情")
    p_info.add_argument("--model", required=True)

    for action in ["start", "pause"]:
        p = sub.add_parser(action)
        p.add_argument("--model", required=True)

    p_train = sub.add_parser("train", help="训练模型")
    p_train.add_argument("--model", required=True)
    p_train.add_argument("--epochs", type=int, default=10)
    p_train.add_argument("--lr", type=float, default=0.001, help="学习率")
    p_train.add_argument("--batch-size", type=int, default=32, dest="batch_size")

    p_infer = sub.add_parser("infer", help="执行推理")
    p_infer.add_argument("--model", required=True)
    p_infer.add_argument("--input", default="{}", help="JSON格式输入数据")

    p_hist = sub.add_parser("history", help="推理历史")
    p_hist.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.cmd == "list":
        result = get_json("/api/models")
        if ok(result):
            models = result if isinstance(result, list) else result.get("models", [])
            print(f"\n🤖 AI模型列表（共 {len(models)} 个）\n")
            print(f"{'ID':<20} {'名称':<25} {'类型':<20} {'状态'}")
            print("-" * 80)
            for m in models:
                mid = m.get("id", m.get("model_id", ""))
                mname = m.get("name", MODEL_CN.get(mid, mid))
                mtype = m.get("model_type", m.get("type", ""))
                mstatus = STATUS_MAP.get(m.get("status", ""), m.get("status", ""))
                print(f"{mid:<20} {mname:<25} {mtype:<20} {mstatus}")
        else:
            print(f"❌ 获取模型列表失败: {result['error']}")

    elif args.cmd == "info":
        result = get_json(f"/api/models/{args.model}")
        if ok(result):
            print(f"\n📋 模型详情: {MODEL_CN.get(args.model, args.model)}")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 获取详情失败: {result['error']}")

    elif args.cmd == "start":
        result = post_json(f"/api/models/{args.model}/start")
        if ok(result):
            print(f"✅ 模型 {MODEL_CN.get(args.model, args.model)} 已启动")
        else:
            print(f"❌ 启动失败: {result['error']}")

    elif args.cmd == "pause":
        result = post_json(f"/api/models/{args.model}/pause")
        if ok(result):
            print(f"⏸ 模型 {MODEL_CN.get(args.model, args.model)} 已暂停")
        else:
            print(f"❌ 暂停失败: {result['error']}")

    elif args.cmd == "train":
        data = {"epochs": args.epochs, "learning_rate": args.lr, "batch_size": args.batch_size}
        result = post_json(f"/api/models/{args.model}/train", data)
        if ok(result):
            print(f"🏋️ 训练任务已提交:")
            print(f"   模型: {MODEL_CN.get(args.model, args.model)}")
            print(f"   轮次: {args.epochs}  学习率: {args.lr}  批大小: {args.batch_size}")
            task_id = result.get("task_id", result.get("id", ""))
            if task_id:
                print(f"   任务ID: {task_id}")
        else:
            print(f"❌ 训练启动失败: {result['error']}")

    elif args.cmd == "infer":
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError:
            print(f"❌ 输入数据不是有效JSON: {args.input}")
            sys.exit(1)
        data = {"model_id": args.model, "input_data": input_data, "options": {}}
        result = post_json("/api/inference/execute", data)
        if ok(result):
            print(f"🧠 推理完成 [{MODEL_CN.get(args.model, args.model)}]:")
            output = result.get("output", result.get("result", result))
            print(json.dumps(output, ensure_ascii=False, indent=2))
            conf = result.get("confidence")
            if conf is not None:
                level = "高" if conf > 0.8 else ("中" if conf > 0.5 else "低")
                print(f"\n   置信度: {conf:.2%} ({level}置信)")
        else:
            print(f"❌ 推理失败: {result['error']}")

    elif args.cmd == "history":
        result = get_json(f"/api/inference/history?limit={args.limit}")
        if ok(result):
            records = result if isinstance(result, list) else result.get("records", [])
            print(f"\n📜 最近 {len(records)} 条推理记录:")
            for i, r in enumerate(records, 1):
                ts = r.get("timestamp", r.get("created_at", ""))
                mid = r.get("model_id", "")
                status = r.get("status", "")
                print(f"  {i:2}. [{ts[:19]}] {MODEL_CN.get(mid,mid)} → {status}")
        else:
            print(f"❌ 获取历史失败: {result['error']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
