"""
AI平台主API应用
集成所有服务模块，提供统一的API接口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# 导入核心服务
from src.core.services import model_manager, inference_engine

# 导入API路由
from src.api.routes import models, ai_control, blockchain, model_manager as model_manager_router
from src.api.routes.cloud_ai import router as cloud_ai_router

def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="AI农业决策系统",
        description="开源AI农业决策平台 - 调用云端大模型，无需本地GPU",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 添加CORS中间件（允许所有来源，方便本地开发）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    app.include_router(models.router, prefix="/api")
    app.include_router(ai_control.router, prefix="/api")
    app.include_router(blockchain.router, prefix="/api")
    app.include_router(model_manager_router.router, prefix="/api")
    app.include_router(cloud_ai_router, prefix="/api")   # 云端 AI 对话
    
    # 健康检查端点
    @app.get("/health")
    async def health_check():
        from src.core.services.cloud_ai_service import get_model_info
        model_info = get_model_info()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "ai_model": model_info,
        }
    
    @app.get("/")
    async def root():
        return {
            "message": "AI农业决策系统 API 运行中",
            "version": "1.0.0",
            "docs": "/docs",
            "github": "https://github.com/maco1979/ai-agriculture-system",
        }
    
    # 应用启动事件
    @app.on_event("startup")
    async def startup_event():
        """应用启动时初始化服务"""
        print("正在初始化模型管理器...")
        try:
            init_result = await model_manager.initialize()
            if init_result.get("success"):
                print("✅ 模型管理器初始化成功")
            else:
                print(f"⚠️  模型管理器初始化跳过: {init_result.get('error', '未知')}")
        except Exception as e:
            print(f"⚠️  模型管理器初始化跳过 (非阻断): {e}")
        
        from src.core.services.cloud_ai_service import get_model_info
        info = get_model_info()
        if info["configured"]:
            print(f"✅ 云端 AI 模型已配置: {info['provider_name']} / {info['model']}")
        else:
            print("⚠️  未配置 AI API Key，请在 .env 中设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        
        print("🌾 AI农业决策系统 API 启动完成")
    
    # 应用关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        print("正在关闭模型管理器...")
        try:
            await model_manager.close()
        except Exception:
            pass
        print("AI平台API已关闭")
    
    return app