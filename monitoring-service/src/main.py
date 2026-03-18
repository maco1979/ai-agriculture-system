"""
监控和日志服务主应用入口
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config.config import settings
from .api.routes.monitoring import router as monitoring_router
from .api.routes.logging import router as logging_router
from .api.routes.alerts import router as alerts_router
from .middleware.security import setup_cors, monitoring_auth_middleware
from .middleware.logger import log_requests, log_exceptions

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("监控和日志服务启动中...")
    
    # 初始化资源
    await initialize_services()
    
    yield
    
    # 关闭时执行
    logger.info("监控和日志服务关闭中...")
    await cleanup_services()


async def initialize_services():
    """初始化服务"""
    logger.info("初始化监控和日志服务...")
    # 这里可以初始化数据库连接、Redis连接等
    logger.info("监控和日志服务初始化完成")


async def cleanup_services():
    """清理服务资源"""
    logger.info("清理监控和日志服务资源...")
    # 这里可以关闭数据库连接、Redis连接等
    logger.info("资源清理完成")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="AI农业平台监控和日志服务微服务",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 设置CORS中间件
setup_cors(app)

# 添加中间件
app.middleware("http")(log_requests)
app.middleware("http")(log_exceptions)
app.middleware("http")(monitoring_auth_middleware)


# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "内部服务器错误",
            "message": str(exc) if settings.debug else "服务内部错误"
        }
    )


# 注册路由
app.include_router(monitoring_router)
app.include_router(logging_router)
app.include_router(alerts_router)


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "environment": "development" if settings.debug else "production"
    }


# 服务信息端点
@app.get("/info")
async def service_info():
    """服务信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI农业平台监控和日志服务微服务",
        "status": "running",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "docs": "/docs",
            "monitoring_api": "/api/monitoring",
            "logging_api": "/api/monitoring/logs",
            "alerts_api": "/api/monitoring/alerts"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动监控和日志服务: {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )