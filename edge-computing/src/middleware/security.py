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


async def node_authentication_middleware(request: Request, call_next):
    """节点认证中间件"""
    if request.url.path.startswith("/api/edge/nodes") and request.method != "GET":
        node_id = request.headers.get("X-Node-ID")
        node_token = request.headers.get("X-Node-Token")
        
        if not node_id or not node_token:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "节点认证信息缺失"}
            )
        
        # 这里可以添加节点认证逻辑
        # 例如验证节点ID和令牌是否匹配
        
        logger.info(f"节点认证: {node_id}")
    
    response = await call_next(request)
    return response
