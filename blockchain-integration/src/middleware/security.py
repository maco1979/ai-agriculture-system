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


async def blockchain_auth_middleware(request: Request, call_next):
    """区块链认证中间件"""
    if request.url.path.startswith("/api/blockchain") and request.method != "GET":
        signature = request.headers.get("X-Blockchain-Signature")
        wallet_address = request.headers.get("X-Wallet-Address")
        
        if not signature or not wallet_address:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "区块链认证信息缺失"}
            )
        
        # 这里可以添加区块链签名验证逻辑
        # 例如验证签名是否与钱包地址匹配
        
        logger.info(f"区块链认证: {wallet_address}")
    
    response = await call_next(request)
    return response
