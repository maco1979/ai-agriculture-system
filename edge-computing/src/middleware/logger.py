"""日志中间件模块"""

from fastapi import Request
from fastapi.responses import Response
import logging
import time
import json
from typing import Callable, Any

logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """记录请求日志"""
    # 开始时间
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"请求开始: {request.method} {request.url}")
    logger.debug(f"请求头: {dict(request.headers)}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(f"请求完成: {request.method} {request.url} - {response.status_code} - {process_time:.4f}秒")
    
    # 添加处理时间头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


async def log_exceptions(request: Request, call_next: Callable[[Request], Any]) -> Response:
    """异常日志中间件"""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # 记录异常信息
        logger.error(f"请求异常: {request.method} {request.url}", exc_info=e)
        raise
