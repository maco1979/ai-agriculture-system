"""安全中间件模块"""

from fastapi import HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import logging
import time

from ..config.config import settings

logger = logging.getLogger(__name__)


def setup_cors(app):
    """设置CORS中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def monitoring_auth_middleware(request: Request, call_next):
    """监控认证中间件"""
    if request.url.path.startswith("/api/monitoring") and request.method != "GET":
        api_key = request.headers.get("X-Monitoring-Key")
        
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "监控API密钥缺失"}
            )
        
        # 这里可以添加监控API密钥验证逻辑
        # 例如验证API密钥是否有效
        
        logger.info(f"监控API认证: {api_key[:8]}...")
    
    response = await call_next(request)
    return response
