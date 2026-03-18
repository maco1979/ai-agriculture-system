"""验证Vite代理：通过3000端口访问后端API"""
import sys
import urllib.request
import urllib.error
import json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FRONTEND = "http://localhost:3000"
BACKEND  = "http://localhost:8001"

def get(url, label):
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        r = urllib.request.urlopen(req, timeout=8)
        content = r.read().decode()
        print(f"[PASS] [{r.status}] {label}")
        return r.status, content
    except urllib.error.HTTPError as e:
        print(f"[FAIL] [{e.code}] {label}")
        return e.code, ""
    except Exception as e:
        print(f"[ERR]  [---] {label}: {e}")
        return 0, ""

print("=" * 60)
print("Vite 代理验证 (3000 -> 8001)")
print("=" * 60)

print("\n[1] 前端页面可访问")
get(f"{FRONTEND}/", "前端首页 localhost:3000/")

print("\n[2] 通过代理访问后端 API")
get(f"{FRONTEND}/api/agriculture/crop-configs", "代理: /api/agriculture/crop-configs")
get(f"{FRONTEND}/api/community/live-streams",   "代理: /api/community/live-streams")
get(f"{FRONTEND}/api/performance/summary",      "代理: /api/performance/summary")
get(f"{FRONTEND}/api/system/health",            "代理: /api/system/health")
get(f"{FRONTEND}/api/models",                   "代理: /api/models")

print("\n[3] 直接访问后端 (对比验证)")
get(f"{BACKEND}/api/agriculture/crop-configs", "直连: /api/agriculture/crop-configs")
get(f"{BACKEND}/api/community/live-streams",   "直连: /api/community/live-streams")

print()
print("=" * 60)
print("代理验证完成")
print("=" * 60)
