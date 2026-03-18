#!/usr/bin/env python3
"""
农业API调用脚本 - OpenClaw技能辅助工具
用法:
  python agriculture-api.py light-formula --crop 番茄 --stage 开花期
  python agriculture-api.py predict --crop 生菜 --stage 苗期 --temp 22 --humidity 70
  python agriculture-api.py plan --crop 黄瓜 --area 100
  python agriculture-api.py recommend --season spring --location 北京
  python agriculture-api.py decision --crop 番茄 --stage 开花期 --temp 26 --humidity 60
"""
import urllib.request
import urllib.error
import json
import sys
import argparse

BASE_URL = "http://localhost:8001"

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()}"}
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

def print_result(result, title="结果"):
    print(f"\n{'='*50}")
    print(f"🌾 {title}")
    print('='*50)
    if "error" in result:
        print(f"❌ 错误: {result['error']}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

def cmd_light_formula(args):
    data = {
        "crop_type": args.crop,
        "growth_stage": args.stage,
        "target_yield": getattr(args, "target", "高产量")
    }
    result = post_json("/api/agriculture/light-formula", data)
    print_result(result, f"{args.crop}({args.stage}) 光配方建议")

def cmd_predict(args):
    data = {
        "crop_type": args.crop,
        "current_stage": args.stage,
        "environment": {
            "temperature": args.temp,
            "humidity": args.humidity,
            "light_hours": getattr(args, "light", 14)
        }
    }
    result = post_json("/api/agriculture/growth-prediction", data)
    print_result(result, f"{args.crop} 生长预测")

def cmd_plan(args):
    from datetime import date
    data = {
        "crop_type": args.crop,
        "area_sqm": args.area,
        "start_date": getattr(args, "date", str(date.today()))
    }
    result = post_json("/api/agriculture/planting-plan", data)
    print_result(result, f"{args.crop} 种植规划")

def cmd_recommend(args):
    path = f"/api/agriculture/crop-recommendations?season={args.season}"
    if hasattr(args, "location") and args.location:
        path += f"&location={args.location}"
    result = get_json(path)
    print_result(result, f"{args.season}季作物推荐")

def cmd_decision(args):
    data = {
        "crop_type": args.crop,
        "growth_stage": args.stage,
        "environment_data": {
            "temperature": getattr(args, "temp", 25),
            "humidity": getattr(args, "humidity", 65)
        }
    }
    result = post_json("/api/decision/agriculture", data)
    print_result(result, f"{args.crop} AI决策建议")

def main():
    parser = argparse.ArgumentParser(description="农业决策API调用工具")
    sub = parser.add_subparsers(dest="command")

    # light-formula
    p1 = sub.add_parser("light-formula", help="获取光配方")
    p1.add_argument("--crop", required=True, help="作物类型")
    p1.add_argument("--stage", required=True, help="生长阶段")
    p1.add_argument("--target", default="高产量", help="目标产量")

    # predict
    p2 = sub.add_parser("predict", help="植物生长预测")
    p2.add_argument("--crop", required=True)
    p2.add_argument("--stage", required=True)
    p2.add_argument("--temp", type=float, default=25.0, help="温度(℃)")
    p2.add_argument("--humidity", type=float, default=65.0, help="湿度(%)")
    p2.add_argument("--light", type=float, default=14.0, help="光照时长(小时)")

    # plan
    p3 = sub.add_parser("plan", help="种植规划")
    p3.add_argument("--crop", required=True)
    p3.add_argument("--area", type=float, default=100.0, help="种植面积(m²)")
    p3.add_argument("--date", default=None, help="开始日期 YYYY-MM-DD")

    # recommend
    p4 = sub.add_parser("recommend", help="作物推荐")
    p4.add_argument("--season", default="spring", choices=["spring","summer","autumn","winter"])
    p4.add_argument("--location", default="", help="地点")

    # decision
    p5 = sub.add_parser("decision", help="AI农业决策")
    p5.add_argument("--crop", required=True)
    p5.add_argument("--stage", default="生长期")
    p5.add_argument("--temp", type=float, default=25.0)
    p5.add_argument("--humidity", type=float, default=65.0)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "light-formula": cmd_light_formula,
        "predict": cmd_predict,
        "plan": cmd_plan,
        "recommend": cmd_recommend,
        "decision": cmd_decision,
    }
    dispatch[args.command](args)

if __name__ == "__main__":
    main()
