"""API模块
包含FastAPI应用和所有路由
"""

import os

# 在导入任何可能使用Flax的模块之前应用补丁
from core.utils.flax_patch import apply_flax_patch
apply_flax_patch()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routes import models_router, inference_router, training_router, system_router, edge_router, federated_router, agriculture_router, decision_router, model_training_decision_router, resource_decision_router, decision_monitoring_router, camera_router, performance_router, blockchain_router, ai_control_router, auth_router, jepa_dtmpc_router, community_router, monitoring_router, cloud_ai_router, health_router, chat_router, provenance_router

# 可选导入用户、企业和任务路由
try:
    from .routes import user_router
except ImportError:
    user_router = None
try:
    from .routes import enterprise_router
except ImportError:
    enterprise_router = None
try:
    from .routes import tasks_router
except ImportError:
    tasks_router = None

# 导入远程执行路由
try:
    from .routes import remote_execution_router
except ImportError:
    remote_execution_router = None

# 导入安全中间件
from middleware.security import (
    InputValidationMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityConfig
)


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    import asyncio
    from core.services import model_manager
    
    # 获取环境变量判断是否为生产环境
    is_production = os.getenv("ENV", "development").lower() == "production"
    
    app = FastAPI(
        title="AI项目API服务",
        description="基于JAX+Flax的最先进AI项目API服务",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 初始化模型管理器 + 启动社区 AI 调度器
    @app.on_event("startup")
    async def startup_event():
        import logging
        _log = logging.getLogger(__name__)

        try:
            await model_manager.initialize()
        except Exception as e:
            _log.warning(
                f"model_manager 初始化失败（非致命），服务继续运行: {e}"
            )

        # 启动社区 AI 自主发帖调度器（定时发帖 + 事件预警）
        try:
            from src.services.community_scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            _log.warning(f"社区调度器启动失败（非致命）: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        try:
            from src.services.community_scheduler import stop_scheduler
            stop_scheduler()
        except Exception:
            pass
    
    # ===== 路径兼容中间件（修复双重/api前缀问题）=====
    @app.middleware("http")
    async def fix_duplicate_api_prefix(request: Request, call_next):
        """自动修复 /api/api/xxx 路径为 /api/xxx"""
        if request.url.path.startswith("/api/api/"):
            request.scope["path"] = request.scope["path"].replace("/api/api/", "/api/", 1)
        response = await call_next(request)
        return response
    
    # ===== 安全中间件配置（注意：FastAPI中间件是后进先出，最后添加的最先执行）=====
    security_config = SecurityConfig()
    
    # ========== 严格CORS配置（核心安全策略）==========
    # 生产环境：严格白名单模式
    # 开发环境：宽松配置（方便调试）
    
    if is_production:
        # 生产环境：严格CORS策略
        # ⚠️ 必须配置实际的生产域名白名单
        production_origins = [
            "https://your-domain.com",
            "https://www.your-domain.com",
            "https://api.your-domain.com",
            # 添加其他生产域名...
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=production_origins,  # ✅ 仅允许白名单域名
            allow_credentials=False,  # ✅ 禁用跨域凭证（防止Cookie泄露）
            allow_methods=["GET", "POST", "PUT", "DELETE"],  # ✅ 限制请求方法
            allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # ✅ 限制请求头
            max_age=86400,  # ✅ 预检请求缓存1天
        )
        print("[CORS] Production mode: strict whitelist")
    else:
        # 开发环境：宽松配置
        development_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8080",
            "http://localhost:5173",  # Vite默认端口
            "http://127.0.0.1:5173",
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=development_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
        )
        print("[CORS] Development mode: relaxed")
    
    # 2. 速率限制中间件（防止暴力攻击）
    # 优化：调高限制以适应WebSocket转换后的请求量减少
    app.add_middleware(
        RateLimitMiddleware, 
        requests_per_minute=300,  # 从120调高到300，配合WebSocket使用
        burst_limit=500  # 从200调高到500
    )
    
    # 3. 输入验证中间件（SQL注入/XSS防护）
    app.add_middleware(InputValidationMiddleware, config=security_config)
    
    # 4. 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)
    
    # 5. 安全响应头中间件（最后添加，最先执行，确保响应头被添加）
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 注册路由到/api前缀下
    app.include_router(models_router, prefix="/api")
    app.include_router(inference_router, prefix="/api")
    app.include_router(training_router, prefix="/api")
    app.include_router(system_router, prefix="/api")
    app.include_router(edge_router, prefix="/api")
    
    # 仅在区块链路由可用时注册
    if blockchain_router:
        app.include_router(blockchain_router, prefix="/api")
        
    app.include_router(federated_router, prefix="/api")
    app.include_router(agriculture_router, prefix="/api")
    app.include_router(decision_router, prefix="/api")
    app.include_router(model_training_decision_router, prefix="/api")
    app.include_router(resource_decision_router, prefix="/api")
    app.include_router(decision_monitoring_router, prefix="/api")
    app.include_router(camera_router, prefix="/api")
    app.include_router(performance_router, prefix="/api")
    app.include_router(ai_control_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(jepa_dtmpc_router, prefix="/api")
    app.include_router(community_router, prefix="/api")
    
    # 注册用户和企业路由
    if user_router:
        app.include_router(user_router, prefix="/api")
    if enterprise_router:
        app.include_router(enterprise_router, prefix="/api")
    
    # 注册监控路由（Prometheus/Grafana集成）
    app.include_router(monitoring_router, prefix="/api")

    # 注册云端 AI 路由（核心功能：/api/ai/chat 等接口）
    app.include_router(cloud_ai_router, prefix="/api")

    # 注册聊天路由（/api/chat/completions 流式对话接口）
    app.include_router(chat_router, prefix="/api")

    # 注册健康检查路由（/health）
    app.include_router(health_router)

    # 注册数据溯源 + PHOTON 奖励路由（/api/provenance/...）
    app.include_router(provenance_router, prefix="/api")

    # 注册任务管理路由（/api/tasks/...）
    if tasks_router is not None:
        app.include_router(tasks_router, prefix="/api")

    # 注册远程命令执行路由（/api/remote/...）
    if remote_execution_router is not None:
        app.include_router(remote_execution_router, prefix="/api/v1")

    # 根路径
    @app.get("/")
    async def root():
        return {
            "message": "AI项目API服务",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    return app


# 创建 FastAPI 应用实例
app = create_app()