#!/usr/bin/env python3
"""
系统监控脚本 - OpenClaw技能辅助工具
用法:
  python sysmon.py health
  python sysmon.py metrics
  python sysmon.py logs [--level INFO] [--limit 50]
  python sysmon.py watch [--interval 5]   # 持续监控模式
"""
import urllib.request
import urllib.error
import json
import sys
import argparse
import time

BASE_URL = "http://localhost:8001"


def get_json(path, timeout=8):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        return {"error": f"连接失败: {e.reason}  (服务是否已启动？)"}
    except Exception as e:
        return {"error": str(e)}


def fmt_bytes(b):
    """将字节数格式化为可读字符串"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def bar(pct, width=20):
    """生成文本进度条"""
    filled = int(width * pct / 100)
    bar_str = "█" * filled + "░" * (width - filled)
    color = ""
    if pct >= 90:
        color = "\033[91m"  # red
    elif pct >= 75:
        color = "\033[93m"  # yellow
    else:
        color = "\033[92m"  # green
    reset = "\033[0m"
    return f"{color}[{bar_str}]{reset} {pct:.1f}%"


def cmd_health(args):
    result = get_json("/api/system/health")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🌾 AI农业系统 — 健康检查")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if "error" in result:
        print(f"  ❌ 服务不可达: {result['error']}")
        print("  💡 启动命令: cd d:/1.6/1.5/backend && python simple_api.py")
        sys.exit(1)

    overall = result.get("status", "unknown")
    emoji = "✅" if overall == "healthy" else "⚠️"
    print(f"  {emoji} 总体状态: {overall.upper()}")
    print(f"  🕐 检查时间: {result.get('timestamp', 'N/A')[:19]}")
    print(f"  📦 版本: {result.get('version', 'N/A')}")

    components = result.get("components", {})
    if components:
        print("\n  📋 组件状态:")
        for name, status in components.items():
            icon = "✅" if status == "healthy" else "❌"
            print(f"    {icon} {name:<25} {status}")
    print()


def cmd_metrics(args):
    result = get_json("/api/system/metrics")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  📊 系统资源指标")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if "error" in result:
        print(f"  ❌ {result['error']}")
        sys.exit(1)

    # CPU
    cpu = result.get("cpu", result)
    cpu_pct = cpu.get("percent", result.get("cpu_percent", 0))
    cpu_count = cpu.get("count", result.get("cpu_count", "N/A"))
    print(f"\n  🖥️  CPU  {bar(cpu_pct)}  ({cpu_count} 核)")

    # 内存
    mem = result.get("memory", result)
    mem_pct = mem.get("percent", result.get("memory_percent", 0))
    mem_used = mem.get("used", result.get("memory_used", 0))
    mem_total = mem.get("total", result.get("memory_total", 0))
    used_str = fmt_bytes(mem_used) if mem_used else "N/A"
    total_str = fmt_bytes(mem_total) if mem_total else "N/A"
    print(f"  🧠 内存  {bar(mem_pct)}  ({used_str} / {total_str})")

    # 磁盘
    disk = result.get("disk", result)
    disk_pct = disk.get("percent", result.get("disk_percent", 0))
    disk_used = disk.get("used", result.get("disk_used", 0))
    disk_total = disk.get("total", result.get("disk_total", 0))
    d_used_str = fmt_bytes(disk_used) if disk_used else "N/A"
    d_total_str = fmt_bytes(disk_total) if disk_total else "N/A"
    print(f"  💾 磁盘  {bar(disk_pct)}  ({d_used_str} / {d_total_str})")

    # 网络
    net = result.get("network", {})
    if net:
        sent = fmt_bytes(net.get("bytes_sent", 0))
        recv = fmt_bytes(net.get("bytes_recv", 0))
        print(f"\n  🌐 网络  ↑ 已发送: {sent}  ↓ 已接收: {recv}")

    print()


def cmd_logs(args):
    path = f"/api/system/logs?level={args.level}&limit={args.limit}"
    result = get_json(path)
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  📜 系统日志  [{args.level}]  最近 {args.limit} 条")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if "error" in result:
        print(f"  ❌ {result['error']}")
        sys.exit(1)

    logs = result if isinstance(result, list) else result.get("logs", [])
    LEVEL_ICONS = {"DEBUG": "🔍", "INFO": "ℹ️ ", "WARNING": "⚠️ ", "ERROR": "❌", "CRITICAL": "🔥"}

    for entry in logs:
        ts = str(entry.get("timestamp", entry.get("time", "")))[:19]
        level = entry.get("level", entry.get("severity", "INFO")).upper()
        msg = entry.get("message", entry.get("msg", str(entry)))
        icon = LEVEL_ICONS.get(level, "•")
        print(f"  {icon} [{ts}] {level:<8} {msg}")

    if not logs:
        print("  （暂无日志记录）")
    print()


def cmd_watch(args):
    """持续监控模式"""
    print(f"  🔄 持续监控模式（每 {args.interval}s 刷新，Ctrl+C 退出）\n")
    try:
        while True:
            cmd_metrics(args)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  已停止监控。")


def main():
    parser = argparse.ArgumentParser(description="AI农业系统 — 系统监控工具")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("health", help="健康检查")
    sub.add_parser("metrics", help="资源指标")

    p_logs = sub.add_parser("logs", help="查看系统日志")
    p_logs.add_argument("--level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    p_logs.add_argument("--limit", type=int, default=50)

    p_watch = sub.add_parser("watch", help="持续监控")
    p_watch.add_argument("--interval", type=int, default=5, help="刷新间隔(秒)")

    args = parser.parse_args()

    dispatch = {
        "health": cmd_health,
        "metrics": cmd_metrics,
        "logs": cmd_logs,
        "watch": cmd_watch,
    }

    if not args.cmd:
        # 默认：综合仪表盘
        cmd_health(args)
        cmd_metrics(args)
    else:
        dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
