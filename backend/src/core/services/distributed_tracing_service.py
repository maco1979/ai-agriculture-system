"""分布式追踪服务
提供请求追踪和性能分析功能
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar

# 直接导入，不使用try-except，以便在导入失败时能看到具体错误
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import inject, extract
_opentelemetry_available = True

from src.config.logging import get_logger

logger = get_logger(__name__)

# 上下文变量，用于存储当前请求的跟踪信息
current_span: ContextVar[Optional[Any]] = ContextVar('current_span', default=None)


class DistributedTracingService:
    """分布式追踪服务"""
    
    def __init__(self):
        """初始化分布式追踪服务"""
        self._tracer_provider = None
        self._initialized = False
        self._opentelemetry_available = _opentelemetry_available
        
        if not self._opentelemetry_available:
            logger.warning("OpenTelemetry库未安装，分布式追踪功能将被禁用")
    
    def initialize(self, service_name: str = "ai-platform"):
        """初始化分布式追踪服务
        
        Args:
            service_name: 服务名称
        """
        if not self._opentelemetry_available:
            return
        
        try:
            # 创建资源
            resource = Resource(
                attributes={
                    SERVICE_NAME: service_name
                }
            )
            
            # 创建追踪提供者
            self._tracer_provider = TracerProvider(resource=resource)
            
            # 配置Jaeger导出器
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_PORT", "6831"))
            )
            
            # 添加批处理 span 处理器
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self._tracer_provider.add_span_processor(span_processor)
            
            # 设置全局追踪提供者
            trace.set_tracer_provider(self._tracer_provider)
            
            # 自动检测常见库
            self._instrument_libraries()
            
            self._initialized = True
            logger.info("分布式追踪服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化分布式追踪服务失败: {e}")
    
    def _instrument_libraries(self):
        """自动检测常见库"""
        if not self._opentelemetry_available:
            return
        
        try:
            # 检测请求库
            RequestsInstrumentor().instrument()
            
            # 检测SQLAlchemy
            try:
                SQLAlchemyInstrumentor().instrument()
            except Exception:
                pass
            
            # 检测Redis
            try:
                RedisInstrumentor().instrument()
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"检测库失败: {e}")
    
    def instrument_fastapi(self, app):
        """检测FastAPI应用
        
        Args:
            app: FastAPI应用实例
        """
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI应用检测完成")
        except Exception as e:
            logger.error(f"检测FastAPI应用失败: {e}")
    
    def get_tracer(self, name: str) -> Optional[Any]:
        """获取追踪器
        
        Args:
            name: 追踪器名称
        
        Returns:
            追踪器实例
        """
        if not self._opentelemetry_available or not self._initialized:
            return None
        
        try:
            return trace.get_tracer(name)
        except Exception as e:
            logger.error(f"获取追踪器失败: {e}")
            return None
    
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """开始一个新的span
        
        Args:
            name: span名称
            attributes: span属性
        
        Returns:
            span实例
        """
        if not self._opentelemetry_available or not self._initialized:
            return None
        
        try:
            tracer = trace.get_tracer(__name__)
            span = tracer.start_as_current_span(name)
            
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            # 更新上下文变量
            current_span.set(span)
            
            return span
        except Exception as e:
            logger.error(f"开始span失败: {e}")
            return None
    
    def end_span(self, span: Optional[Any] = None):
        """结束一个span
        
        Args:
            span: span实例，如果为None则使用当前上下文的span
        """
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            if span:
                span.end()
            else:
                current_span_value = current_span.get()
                if current_span_value:
                    current_span_value.end()
                    current_span.set(None)
        except Exception as e:
            logger.error(f"结束span失败: {e}")
    
    def inject_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """注入追踪上下文到请求头
        
        Args:
            headers: 请求头字典
        
        Returns:
            注入了追踪上下文的请求头
        """
        if not self._opentelemetry_available or not self._initialized:
            return headers
        
        try:
            inject(headers)
            return headers
        except Exception as e:
            logger.error(f"注入追踪上下文失败: {e}")
            return headers
    
    def extract_context(self, headers: Dict[str, str]):
        """从请求头提取追踪上下文
        
        Args:
            headers: 请求头字典
        """
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            extract(headers)
        except Exception as e:
            logger.error(f"提取追踪上下文失败: {e}")
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """添加事件到当前span
        
        Args:
            name: 事件名称
            attributes: 事件属性
        """
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            span = current_span.get()
            if span:
                span.add_event(name, attributes)
        except Exception as e:
            logger.error(f"添加事件失败: {e}")
    
    def set_attribute(self, key: str, value: Any):
        """设置span属性
        
        Args:
            key: 属性键
            value: 属性值
        """
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            span = current_span.get()
            if span:
                span.set_attribute(key, value)
        except Exception as e:
            logger.error(f"设置span属性失败: {e}")
    
    def shutdown(self):
        """关闭分布式追踪服务"""
        if not self._opentelemetry_available or not self._initialized:
            return
        
        try:
            if self._tracer_provider:
                self._tracer_provider.shutdown()
            self._initialized = False
            logger.info("分布式追踪服务已关闭")
        except Exception as e:
            logger.error(f"关闭分布式追踪服务失败: {e}")


def tracing_decorator(name: str):
    """追踪装饰器
    
    Args:
        name: span名称
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            tracing_service = get_distributed_tracing_service()
            span = tracing_service.start_span(name)
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                tracing_service.add_event("error", {"error": str(e)})
                raise
            finally:
                tracing_service.end_span(span)
        
        def sync_wrapper(*args, **kwargs):
            tracing_service = get_distributed_tracing_service()
            span = tracing_service.start_span(name)
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                tracing_service.add_event("error", {"error": str(e)})
                raise
            finally:
                tracing_service.end_span(span)
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator


# 全局分布式追踪服务实例
_distributed_tracing_service: Optional[DistributedTracingService] = None


def get_distributed_tracing_service() -> DistributedTracingService:
    """获取分布式追踪服务单例"""
    global _distributed_tracing_service
    if _distributed_tracing_service is None:
        _distributed_tracing_service = DistributedTracingService()
    return _distributed_tracing_service


def initialize_tracing(service_name: str = "ai-platform"):
    """初始化分布式追踪服务"""
    service = get_distributed_tracing_service()
    service.initialize(service_name)


def shutdown_tracing():
    """关闭分布式追踪服务"""
    service = get_distributed_tracing_service()
    service.shutdown()


__all__ = [
    "DistributedTracingService",
    "get_distributed_tracing_service",
    "initialize_tracing",
    "shutdown_tracing",
    "tracing_decorator"
]
