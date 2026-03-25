#!/usr/bin/env python3
"""
本地轻量启动入口 — 跳过 JAX/Flax/硬件重依赖
直接可用，适合本地开发调试
"""
import sys
import os
import types

# ─── 0. 路径设置 ──────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ─── 1. Mock 掉无法在本地安装的重依赖 ────────────────────────────────
HEAVY_MOCKS = [
    "jax", "jax.numpy", "jax.random", "jax.lax",
    "jaxlib", "jaxlib.xla_extension",
    "flax", "flax.linen", "flax.linen.compat", "flax.training",
    "optax",
    "ultralytics",
    "cv2",
    "pyserial", "serial",
    "grpcio", "grpc",
    "celery",
]

for mod_name in HEAVY_MOCKS:
    if mod_name not in sys.modules:
        mock = types.ModuleType(mod_name)
        # 让 import jax.numpy as jnp; jnp.array(...) 不报错
        mock.__spec__ = None
        # 返回 MagicMock-like 对象处理任意属性访问
        class _AnyAttr:
            def __getattr__(self, name):
                return _AnyAttr()
            def __call__(self, *a, **kw):
                return _AnyAttr()
            def __iter__(self):
                return iter([])
            def __len__(self):
                return 0
            def __bool__(self):
                return True
        mock.__getattr__ = lambda name: _AnyAttr()
        sys.modules[mod_name] = mock

# jax.numpy 特别处理 — 常用 numpy 替代
import numpy as _np
_jnp_mock = sys.modules["jax.numpy"]
for attr in dir(_np):
    try:
        setattr(_jnp_mock, attr, getattr(_np, attr))
    except Exception:
        pass

# ─── 2. 加载 .env ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    print("[OK] .env 已加载")
except ImportError:
    print("[WARN] python-dotenv 未安装，跳过 .env 加载")

# 强制开发模式
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DISABLE_AI_MODELS", "True")
os.environ.setdefault("DISABLE_BLOCKCHAIN", "True")
os.environ.setdefault("DISABLE_CAMERA", "True")

# ─── 3. 创建精简 FastAPI 应用 ─────────────────────────────────────────
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

app = FastAPI(
    title="AI 农业决策系统 API（本地模式）",
    description="本地开发用精简启动，重型 AI 功能以 Mock 替代",
    version="1.0.0-local",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000",
                   "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 4. 注册路由（逐个 try，单个失败不影响其他）────────────────────
registered = []
failed = []

def _try_register(router_path: str, prefix: str, label: str):
    try:
        # 动态导入路由模块
        parts = router_path.split(".")
        mod_name = ".".join(parts[:-1])
        attr_name = parts[-1]
        import importlib
        mod = importlib.import_module(mod_name)
        router = getattr(mod, attr_name)
        app.include_router(router, prefix=prefix)
        registered.append(label)
    except Exception as e:
        failed.append(f"{label}: {e}")

_try_register("src.api.routes.auth", "/api", "auth")
_try_register("src.api.routes.decision", "/api", "decision")
_try_register("src.api.routes.camera", "/api", "camera")
_try_register("src.api.routes.model_training_decision", "/api", "model_training_decision")

# ─── 5. 基础健康检查端点（始终可用）──────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "AI 农业决策系统 API（本地模式）",
        "version": "1.0.0-local",
        "mode": "development",
        "docs": "/docs",
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "local-simple",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "registered_routers": registered,
        "failed_routers": len(failed),
    }

@app.get("/api/health")
async def api_health():
    return {"status": "ok", "service": "ai-agriculture-backend", "mode": "local"}

# Mock 端点 — 让前端仪表盘不报 404
@app.get("/api/models")
async def list_models():
    return {"models": [], "total": 0, "message": "本地模式：模型功能已禁用"}

@app.get("/api/system/status")
async def system_status():
    return {
        "status": "running",
        "mode": "local",
        "cpu_usage": 0,
        "memory_usage": 0,
        "gpu_available": False,
    }

@app.get("/api/monitoring/metrics")
async def metrics():
    return {"metrics": [], "message": "本地模式"}

@app.get("/api/agriculture/crops")
async def crops():
    return {
        "crops": [
            {"id": 1, "name": "番茄", "status": "生长中", "health": 92},
            {"id": 2, "name": "生菜", "status": "生长中", "health": 88},
            {"id": 3, "name": "辣椒", "status": "待播种", "health": 100},
        ]
    }

# ─── 6. 启动 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("\n" + "═" * 60)
    print("  AI 农业决策系统后端  [本地精简模式]")
    print("═" * 60)
    print(f"  地址:   http://localhost:8001")
    print(f"  文档:   http://localhost:8001/docs")
    print(f"  已注册路由: {registered or ['基础端点']}")
    if failed:
        print(f"  跳过路由 ({len(failed)} 个，重依赖未安装):")
        for f in failed[:5]:
            print(f"    - {f[:80]}")
    print("═" * 60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )
