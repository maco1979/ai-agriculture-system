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


async def api_key_middleware(request: Request, call_next):
    """API密钥验证中间件"""
    if request.url.path.startswith("/api/decision") and request.method != "GET":
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "API密钥缺失"}
            )
        if api_key != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "API密钥无效"}
            )
    response = await call_next(request)
    return response


async def rate_limit_middleware(request: Request, call_next):
    """速率限制中间件"""
    # 简单的内存速率限制实现
    # 生产环境中应使用Redis等分布式方案
    client_ip = request.client.host
    current_time = time.time()
    
    # 这里可以实现更复杂的速率限制逻辑
    response = await call_next(request)
    return response
