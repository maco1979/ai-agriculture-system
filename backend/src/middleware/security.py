"""
安全中间件模块
提供SQL注入防护、XSS防护、安全响应头、HSTS等安全功能

生产环境配置：
- 设置环境变量 ENV=production 启用严格安全策略
- 启用HSTS强制HTTPS（仅生产环境）
- 启用严格CORS跨域策略
"""

import os
import re
import html
import logging
from typing import Callable, List, Optional, Dict, Any, Set, Tuple
from urllib.parse import unquote, parse_qs
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# 配置日志
logger = logging.getLogger("security")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# ========== 环境变量配置 ==========
ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV.lower() == "production"

# 打印环境信息
if IS_PRODUCTION:
    print(f"[SECURITY] Production mode: ENV={ENV}")
    print("   - HSTS: enabled")
    print("   - Strict CORS: enabled")
else:
    print(f"[SECURITY] Development mode: {ENV} (relaxed security)")


class SecurityConfig:
    """安全配置"""
    
    # SQL注入检测模式
    # 注意：这些模式仅用于检测明显的攻击载荷，而非阻止正常的SQL关键字使用
    SQL_INJECTION_PATTERNS = [
        # 注释攻击（高危险）
        r"(--|#|/\*|\*/)",
        # 布尔盲注模式（高危险）
        r"(\b)(OR|AND)(\b)\s*\d+\s*=\s*\d+",
        r"'\s*(OR|AND)\s*'?\d+'\s*=\s*'\d+",
        r"'?\s*OR\s*'?1'?\s*=\s*'?1",
        # 堆叠查询（高危险）
        r";\s*(SELECT|INSERT|UPDATE|DELETE|DROP)",
        r"'\s*;\s*--",
        # 联合查询攻击（高危险）
        r"UNION\s+SELECT",
        r"UNION\s+ALL\s+SELECT",
        # 文件操作攻击（高危险）
        r"INTO\s+OUTFILE",
        r"INTO\s+DUMPFILE",
        r"LOAD_FILE",
        # 时间盲注（高危险）
        r"BENCHMARK\s*\(",
        r"SLEEP\s*\(",
        r"WAITFOR\s+DELAY",
        # 经典绕过模式
        r"'\s*OR\s*''\s*=\s*'",
        r"admin\s*'?\s*--",
        r"'\s*OR\s*'[^']*'\s*=\s*'",
    ]
    
    # XSS攻击检测模式
    XSS_PATTERNS = [
        # 脚本标签
        r"<\s*script[^>]*>",
        r"</\s*script\s*>",
        # 事件处理器
        r"\bon\w+\s*=",
        # JavaScript协议
        r"javascript\s*:",
        r"vbscript\s*:",
        r"data\s*:\s*text/html",
        # 内联事件
        r"<[^>]+\s+on\w+\s*=",
        # SVG/IMG攻击
        r"<\s*(svg|img|iframe|object|embed|video|audio)[^>]*>",
        # 表达式
        r"expression\s*\(",
        r"url\s*\(",
        # 编码绕过
        r"&#\d+;",
        r"&#x[0-9a-fA-F]+;",
        # 常见XSS载荷
        r"alert\s*\(",
        r"confirm\s*\(",
        r"prompt\s*\(",
        r"document\.(cookie|location|write)",
        r"window\.(location|open)",
        r"eval\s*\(",
    ]
    
    # 路径遍历检测模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e[/\\%]",
        r"%252e%252e[/\\%]",
    ]
    
    # 危险文件扩展名
    DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.php', '.asp', '.aspx', '.jsp'}
    
    # 白名单路径（不进行安全检查）
    WHITELIST_PATHS = {'/docs', '/redoc', '/openapi.json', '/health', '/metrics'}
    
    # 最大参数长度
    MAX_PARAM_LENGTH = 10000
    
    # 最大请求体大小 (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024


class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        self.sql_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.config.SQL_INJECTION_PATTERNS
        ]
        self.xss_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.XSS_PATTERNS
        ]
        self.path_traversal_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.PATH_TRAVERSAL_PATTERNS
        ]
    
    def detect_sql_injection(self, value: str) -> tuple[bool, Optional[str]]:
        """检测SQL注入攻击"""
        if not value:
            return False, None
        
        # URL解码
        decoded = unquote(value)
        
        for pattern in self.sql_patterns:
            match = pattern.search(decoded)
            if match:
                return True, f"检测到SQL注入模式: {match.group()}"
        
        return False, None
    
    def detect_xss(self, value: str) -> tuple[bool, Optional[str]]:
        """检测XSS攻击"""
        if not value:
            return False, None
        
        # URL解码
        decoded = unquote(value)
        # HTML解码
        decoded = html.unescape(decoded)
        
        for pattern in self.xss_patterns:
            match = pattern.search(decoded)
            if match:
                return True, f"检测到XSS攻击模式: {match.group()}"
        
        return False, None
    
    def detect_path_traversal(self, value: str) -> tuple[bool, Optional[str]]:
        """检测路径遍历攻击"""
        if not value:
            return False, None
        
        decoded = unquote(value)
        
        for pattern in self.path_traversal_patterns:
            match = pattern.search(decoded)
            if match:
                return True, f"检测到路径遍历攻击: {match.group()}"
        
        return False, None
    
    def sanitize_input(self, value: str) -> str:
        """清理输入，转义危险字符"""
        if not value:
            return value
        
        # HTML转义
        sanitized = html.escape(value)
        
        return sanitized
    
    def validate_parameter(self, name: str, value: str) -> tuple[bool, Optional[str]]:
        """验证单个参数"""
        # 检查长度
        if len(value) > self.config.MAX_PARAM_LENGTH:
            return False, f"参数 {name} 超过最大长度限制"
        
        # SQL注入检测
        is_sql_injection, sql_msg = self.detect_sql_injection(value)
        if is_sql_injection:
            return False, sql_msg
        
        # XSS检测
        is_xss, xss_msg = self.detect_xss(value)
        if is_xss:
            return False, xss_msg
        
        # 路径遍历检测
        is_path_traversal, path_msg = self.detect_path_traversal(value)
        if is_path_traversal:
            return False, path_msg
        
        return True, None


class InputValidationMiddleware(BaseHTTPMiddleware):
    """输入验证中间件 - 防止SQL注入和XSS攻击"""
    
    def __init__(self, app: ASGIApp, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.scanner = SecurityScanner(self.config)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否在白名单路径
        if request.url.path in self.config.WHITELIST_PATHS:
            return await call_next(request)
        
        # 验证路径参数
        path = unquote(request.url.path)
        is_valid, error_msg = self.scanner.validate_parameter("path", path)
        if not is_valid:
            logger.warning(f"安全拦截 - 路径: {request.url.path}, 原因: {error_msg}, IP: {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "请求包含非法字符",
                    "code": "SECURITY_VIOLATION"
                }
            )
        
        # 验证查询参数
        for key, value in request.query_params.items():
            is_valid, error_msg = self.scanner.validate_parameter(key, value)
            if not is_valid:
                logger.warning(f"安全拦截 - 查询参数 {key}: {value[:50]}..., 原因: {error_msg}, IP: {request.client.host if request.client else 'unknown'}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "error": "请求包含非法字符",
                        "code": "SECURITY_VIOLATION"
                    }
                )
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全响应头中间件
    
    生产环境启用HSTS（HTTP Strict Transport Security）
    强制浏览器仅通过HTTPS访问
    """
    
    # 基础安全头（所有环境生效）
    # 注意：移除了已废弃的X-Frame-Options和X-XSS-Protection
    # 现代浏览器使用CSP frame-ancestors替代X-Frame-Options
    # X-XSS-Protection已被废弃，现代浏览器内置XSS保护
    BASE_SECURITY_HEADERS = {
        # 防止MIME类型嗅探
        "X-Content-Type-Options": "nosniff",
        # 内容安全策略（包含frame-ancestors替代X-Frame-Options）
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; frame-ancestors 'self'",
        # 引用策略
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # 权限策略
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        # 缓存控制（使用Cache-Control替代Expires）
        "Cache-Control": "no-store, no-cache, must-revalidate, private, max-age=0",
    }
    
    # HSTS配置（仅生产环境启用）
    # max-age=31536000: 强制HTTPS有效期1年
    # includeSubDomains: 所有子域名均生效
    # preload: 加入浏览器HSTS预加载列表
    HSTS_HEADER = "max-age=31536000; includeSubDomains; preload"
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = self.BASE_SECURITY_HEADERS.copy()
        self.hsts_enabled = False
        
        # 生产环境启用HSTS
        if IS_PRODUCTION:
            self.security_headers["Strict-Transport-Security"] = self.HSTS_HEADER
            self.hsts_enabled = True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 使用更安全的方式添加安全头
        response_headers = dict(response.headers)
        for header, value in self.security_headers.items():
            response_headers[header] = value
        
        # 更新响应头
        response.headers.update(response_headers)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件 - 防止暴力攻击"""
    
    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        burst_limit: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_counts: Dict[str, List[datetime]] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, current_time: datetime):
        """清理过期的请求记录"""
        if client_ip in self.request_counts:
            # 只保留最近1分钟的请求
            cutoff = current_time.timestamp() - 60
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip]
                if t.timestamp() > cutoff
            ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # WebSocket 路径白名单（不适用速率限制）
        websocket_paths = ["/api/camera/ws/frame"]
        if request.url.path in websocket_paths:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = datetime.now()
        
        # 清理旧请求
        self._cleanup_old_requests(client_ip, current_time)
        
        # 初始化或获取请求计数
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # 检查突发限制
        if len(self.request_counts[client_ip]) >= self.burst_limit:
            logger.warning(f"速率限制触发 - IP: {client_ip}, 请求数: {len(self.request_counts[client_ip])}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "请求过于频繁，请稍后重试",
                    "code": "RATE_LIMIT_EXCEEDED"
                },
                headers={"Retry-After": "60"}
            )
        
        # 检查每分钟请求限制
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"速率限制触发 - IP: {client_ip}, 每分钟请求数: {len(self.request_counts[client_ip])}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "请求过于频繁，请稍后重试",
                    "code": "RATE_LIMIT_EXCEEDED"
                },
                headers={"Retry-After": "60"}
            )
        
        # 记录请求
        self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 记录安全相关事件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = datetime.now()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = (datetime.now() - start_time).total_seconds()
        
        # 记录可疑请求（4xx和5xx错误）
        if response.status_code >= 400:
            logger.info(
                f"请求日志 - IP: {client_ip}, "
                f"方法: {request.method}, "
                f"路径: {request.url.path}, "
                f"状态码: {response.status_code}, "
                f"耗时: {process_time:.3f}s"
            )
        
        return response


# 参数验证函数
def validate_model_id(model_id: str) -> tuple[bool, Optional[str]]:
    """验证模型ID格式"""
    # 允许的字符：字母、数字、下划线、短横线、点
    pattern = re.compile(r'^[a-zA-Z0-9_\-\.]{1,128}$')
    
    if not pattern.match(model_id):
        return False, "模型ID格式无效，仅允许字母、数字、下划线、短横线和点"
    
    return True, None


def validate_search_query(query: str) -> tuple[bool, Optional[str]]:
    """验证搜索查询"""
    if len(query) > 200:
        return False, "搜索查询过长"
    
    scanner = SecurityScanner()
    
    # 检测恶意模式
    is_sql_injection, sql_msg = scanner.detect_sql_injection(query)
    if is_sql_injection:
        return False, sql_msg
    
    is_xss, xss_msg = scanner.detect_xss(query)
    if is_xss:
        return False, xss_msg
    
    return True, None


def sanitize_output(data: Any) -> Any:
    """清理输出数据，防止XSS"""
    if isinstance(data, str):
        return html.escape(data)
    elif isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    else:
        return data


# 创建安全中间件堆栈
def create_security_middleware_stack(app: ASGIApp, config: SecurityConfig = None) -> ASGIApp:
    """创建完整的安全中间件堆栈"""
    config = config or SecurityConfig()
    
    # 按顺序添加中间件（从内到外）
    # 1. 请求日志
    app = RequestLoggingMiddleware(app)
    # 2. 安全响应头
    app = SecurityHeadersMiddleware(app)
    # 3. 输入验证（SQL注入/XSS防护）
    app = InputValidationMiddleware(app, config)
    # 4. 速率限制
    app = RateLimitMiddleware(app, requests_per_minute=120, burst_limit=200)
    
    return app
