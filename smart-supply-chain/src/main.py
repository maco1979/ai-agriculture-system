# 智能供应链管理服务主入口文件
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务生命周期管理"""
    # 启动时执行
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # 初始化数据库连接
    try:
        # 这里可以添加数据库连接初始化代码
        logger.info("Database connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
    
    # 初始化Redis连接
    try:
        # 这里可以添加Redis连接初始化代码
        logger.info("Redis connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")
    
    yield
    
    # 关闭时执行
    logger.info(f"Shutting down {settings.SERVICE_NAME}")
    # 这里可以添加资源清理代码


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION
    }


# 服务信息端点
@app.get("/info")
async def service_info():
    """服务信息端点"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "description": "智能供应链管理服务，提供供应链优化、物流管理、需求预测等功能",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "api": settings.API_PREFIX
        }
    }


# 注册路由
from api.routes import supply_chain
app.include_router(
    supply_chain.router,
    prefix=settings.API_PREFIX,
    tags=["supply-chain"]
)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
