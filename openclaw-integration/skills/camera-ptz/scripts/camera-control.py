#!/usr/bin/env python3
"""
摄像头与PTZ云台控制脚本 - OpenClaw技能辅助工具
用法:
  python camera-control.py list
  python camera-control.py start --camera cam_001
  python camera-control.py stop --camera cam_001
  python camera-control.py frame --camera cam_001 [--save output.png]
  python camera-control.py ptz-move --camera cam_001 --direction left --speed 5
  python camera-control.py ptz-zoom --camera cam_001 --zoom-in --speed 3
  python camera-control.py ptz-save-preset --camera cam_001 --preset 1 --name "区域A"
  python camera-control.py ptz-goto-preset --camera cam_001 --preset 1
  python camera-control.py ptz-track --camera cam_001 --enable --target crop
  python camera-control.py recognize --camera cam_001 --task crop_classification
"""
import urllib.request
import urllib.error
import json
import sys
import argparse
import base64
import os

BASE_URL = "http://localhost:8001"

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data, ensure_ascii=False).encode()
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

def ok(result):
    return "error" not in result

def main():
    parser = argparse.ArgumentParser(description="摄像头与PTZ云台控制")
    sub = parser.add_subparsers(dest="cmd")

    # list
    sub.add_parser("list", help="列出所有摄像头")

    # start / stop
    for action in ["start", "stop"]:
        p = sub.add_parser(action)
        p.add_argument("--camera", required=True, help="摄像头ID")

    # frame
    pf = sub.add_parser("frame", help="获取当前画面")
    pf.add_argument("--camera", required=True)
    pf.add_argument("--save", default=None, help="保存图片路径 (如 frame.png)")

    # ptz-move
    pm = sub.add_parser("ptz-move", help="PTZ方向控制")
    pm.add_argument("--camera", required=True)
    pm.add_argument("--direction", required=True,
                    choices=["up","down","left","right","stop"], help="移动方向")
    pm.add_argument("--speed", type=int, default=5, help="速度 1-10")

    # ptz-zoom
    pz = sub.add_parser("ptz-zoom", help="PTZ变焦控制")
    pz.add_argument("--camera", required=True)
    group = pz.add_mutually_exclusive_group(required=True)
    group.add_argument("--zoom-in", action="store_true", dest="zoom_in")
    group.add_argument("--zoom-out", action="store_false", dest="zoom_in")
    pz.add_argument("--speed", type=int, default=3)

    # ptz-save-preset
    ps = sub.add_parser("ptz-save-preset", help="保存预置位")
    ps.add_argument("--camera", required=True)
    ps.add_argument("--preset", type=int, required=True, help="预置位编号 (1-255)")
    ps.add_argument("--name", default="", help="预置位名称")

    # ptz-goto-preset
    pg = sub.add_parser("ptz-goto-preset", help="跳转预置位")
    pg.add_argument("--camera", required=True)
    pg.add_argument("--preset", type=int, required=True)

    # ptz-track
    pt = sub.add_parser("ptz-track", help="自动跟踪")
    pt.add_argument("--camera", required=True)
    pt_group = pt.add_mutually_exclusive_group(required=True)
    pt_group.add_argument("--enable", action="store_true")
    pt_group.add_argument("--disable", action="store_false", dest="enable")
    pt.add_argument("--target", default="crop",
                    choices=["crop","person","animal","vehicle"])

    # recognize
    pr = sub.add_parser("recognize", help="视觉识别")
    pr.add_argument("--camera", required=True)
    pr.add_argument("--task", default="crop_classification",
                    choices=["crop_classification","pest_detection","growth_stage"])

    args = parser.parse_args()

    # ──────────── 命令分发 ────────────
    if args.cmd == "list":
        result = get_json("/api/camera/cameras")
        if ok(result):
            cameras = result if isinstance(result, list) else result.get("cameras", [])
            print(f"📷 共发现 {len(cameras)} 个摄像头:")
            for c in cameras:
                cid = c.get("id", c.get("camera_id", "未知"))
                cname = c.get("name", "")
                cstatus = c.get("status", "")
                print(f"  • {cid}  {cname}  [{cstatus}]")
        else:
            print(f"❌ 获取摄像头列表失败: {result['error']}")

    elif args.cmd == "start":
        result = post_json("/api/camera/start", {"camera_id": args.camera})
        if ok(result):
            print(f"✅ 摄像头 {args.camera} 已开启")
        else:
            print(f"❌ 开启失败: {result['error']}")

    elif args.cmd == "stop":
        result = post_json("/api/camera/stop", {"camera_id": args.camera})
        if ok(result):
            print(f"✅ 摄像头 {args.camera} 已关闭")
        else:
            print(f"❌ 关闭失败: {result['error']}")

    elif args.cmd == "frame":
        result = get_json(f"/api/camera/frame?camera_id={args.camera}")
        if ok(result):
            frame_b64 = result.get("frame") or result.get("image")
            if frame_b64 and args.save:
                img_data = base64.b64decode(frame_b64)
                with open(args.save, "wb") as f:
                    f.write(img_data)
                print(f"✅ 画面已保存到: {os.path.abspath(args.save)}")
            else:
                ts = result.get("timestamp", "")
                mode = "模拟" if result.get("simulated") else "真实"
                print(f"✅ 已获取摄像头 {args.camera} 画面 [{mode}模式] {ts}")
                print(f"   图像大小: {len(frame_b64) if frame_b64 else 0} 字节(Base64)")
        else:
            print(f"❌ 获取画面失败: {result['error']}")

    elif args.cmd == "ptz-move":
        result = post_json("/api/camera/ptz/move", {
            "camera_id": args.camera,
            "direction": args.direction,
            "speed": args.speed
        })
        dir_cn = {"up":"上","down":"下","left":"左","right":"右","stop":"停止"}
        if ok(result):
            print(f"✅ PTZ云台向{dir_cn.get(args.direction,args.direction)}移动，速度{args.speed}")
        else:
            print(f"❌ PTZ移动失败: {result['error']}")

    elif args.cmd == "ptz-zoom":
        action = "放大" if args.zoom_in else "缩小"
        result = post_json("/api/camera/ptz/zoom", {
            "camera_id": args.camera,
            "zoom_in": args.zoom_in,
            "speed": args.speed
        })
        if ok(result):
            print(f"✅ 镜头{action}，速度{args.speed}")
        else:
            print(f"❌ 变焦失败: {result['error']}")

    elif args.cmd == "ptz-save-preset":
        result = post_json("/api/camera/ptz/preset/save", {
            "camera_id": args.camera,
            "preset_id": args.preset,
            "name": args.name
        })
        if ok(result):
            print(f"✅ 已保存预置位 {args.preset}（{args.name}）")
        else:
            print(f"❌ 保存预置位失败: {result['error']}")

    elif args.cmd == "ptz-goto-preset":
        result = post_json("/api/camera/ptz/preset/goto", {
            "camera_id": args.camera,
            "preset_id": args.preset
        })
        if ok(result):
            print(f"✅ 已跳转到预置位 {args.preset}")
        else:
            print(f"❌ 跳转失败: {result['error']}")

    elif args.cmd == "ptz-track":
        result = post_json("/api/camera/ptz/auto-track", {
            "camera_id": args.camera,
            "enabled": args.enable,
            "target_type": args.target
        })
        action = "开启" if args.enable else "关闭"
        target_cn = {"crop":"作物","person":"人员","animal":"动物","vehicle":"车辆"}
        if ok(result):
            print(f"✅ 已{action}自动跟踪（目标：{target_cn.get(args.target, args.target)}）")
        else:
            print(f"❌ 跟踪设置失败: {result['error']}")

    elif args.cmd == "recognize":
        result = post_json("/api/camera/recognize", {
            "camera_id": args.camera,
            "task": args.task
        })
        task_cn = {
            "crop_classification": "作物分类",
            "pest_detection": "病虫害检测",
            "growth_stage": "生长阶段判断"
        }
        if ok(result):
            print(f"✅ {task_cn.get(args.task, args.task)} 结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 识别失败: {result['error']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
