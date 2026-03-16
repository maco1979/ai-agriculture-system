"""
优化的数据库查询工具
提供查询缓存、批量查询、并发控制等功能
"""

import asyncio
import threading
from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from functools import wraps
from .enhanced_cache import enhanced_cache_manager, get_enhanced_cache, set_enhanced_cache

T = TypeVar('T')


class QueryCache(Generic[T]):
    """查询缓存"""
    
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        """初始化查询缓存
        
        Args:
            ttl: 缓存过期时间（秒）
            max_size: 最大缓存项数量
        """
        self._ttl = ttl
        self._max_size = max_size
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存的查询结果
        
        Args:
            key: 查询缓存键
        
        Returns:
            Optional[T]: 查询结果
        """
        return get_enhanced_cache(key)
    
    def set(self, key: str, value: T, tags: Optional[List[str]] = None) -> None:
        """设置查询结果缓存
        
        Args:
            key: 查询缓存键
            value: 查询结果
            tags: 缓存标签
        """
        set_enhanced_cache(key, value, self._ttl, tags)
    
    def delete(self, key: str) -> None:
        """删除查询缓存
        
        Args:
            key: 查询缓存键
        """
        from .enhanced_cache import delete_enhanced_cache
        delete_enhanced_cache(key)
    
    def clear(self) -> None:
        """清空所有查询缓存"""
        from .enhanced_cache import clear_enhanced_cache
        clear_enhanced_cache()


class QueryManager:
    """查询管理器"""
    
    def __init__(self, concurrency_limit: int = 10):
        """初始化查询管理器
        
        Args:
            concurrency_limit: 查询并发限制，默认为10
        """
        self._concurrency_limit = concurrency_limit
        self._semaphore = asyncio.Semaphore(concurrency_limit)
        self._query_cache = QueryCache()
        self._lock = threading.RLock()
    
    async def execute_query(self, query_key: str, query_func: Callable[[], Any], ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> Any:
        """执行查询并缓存结果
        
        Args:
            query_key: 查询缓存键
            query_func: 查询函数
            ttl: 缓存过期时间（秒）
            tags: 缓存标签
        
        Returns:
            Any: 查询结果
        """
        # 尝试从缓存获取
        cached_result = self._query_cache.get(query_key)
        if cached_result is not None:
            return cached_result
        
        # 执行查询
        async with self._semaphore:
            result = await query_func()
            
            # 缓存结果
            self._query_cache.set(query_key, result, tags)
            return result
    
    async def execute_batch_queries(self, queries: List[Dict[str, Any]]) -> List[Any]:
        """批量执行查询
        
        Args:
            queries: 查询列表，每个查询包含query_key、query_func、ttl（可选）、tags（可选）
        
        Returns:
            List[Any]: 查询结果列表
        """
        tasks = []
        
        for query in queries:
            query_key = query['query_key']
            query_func = query['query_func']
            ttl = query.get('ttl')
            tags = query.get('tags')
            
            # 尝试从缓存获取
            cached_result = self._query_cache.get(query_key)
            if cached_result is not None:
                tasks.append(asyncio.create_task(asyncio.sleep(0, result=cached_result)))
            else:
                # 创建查询任务
                async def create_task():
                    async with self._semaphore:
                        result = await query_func()
                        self._query_cache.set(query_key, result, tags)
                        return result
                
                tasks.append(create_task())
        
        # 执行所有任务
        results = await asyncio.gather(*tasks)
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        from .enhanced_cache import enhanced_cache_manager
        return enhanced_cache_manager.get_stats()
    
    def set_concurrency_limit(self, limit: int) -> None:
        """设置并发限制
        
        Args:
            limit: 并发限制
        """
        self._concurrency_limit = limit
        self._semaphore = asyncio.Semaphore(limit)


# 全局查询管理器实例
query_manager = QueryManager()


# 优化的查询装饰器
def optimized_query(ttl: int = 300, tags: Optional[List[str]] = None, cache_key: Optional[Callable[..., str]] = None):
    """优化的查询装饰器
    
    示例用法：
    @optimized_query(ttl=60, tags=["user"])
    async def get_user(user_id):
        # 从数据库获取用户信息
        return await db.query(User).filter(User.id == user_id).first()
    
    @optimized_query(ttl=300, tags=["device"], cache_key=lambda device_id: f"device:{device_id}")
    async def get_device(device_id):
        # 从数据库获取设备信息
        return await db.query(Device).filter(Device.id == device_id).first()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """异步查询函数包装器"""
            # 生成缓存键
            if cache_key:
                query_key = cache_key(*args, **kwargs)
            else:
                # 自动生成缓存键
                import hashlib
                key_parts = [func.__name__]
                
                # 处理参数
                for arg in args:
                    key_parts.append(str(arg))
                
                # 处理关键字参数
                for key, value in sorted(kwargs.items()):
                    key_parts.append(f"{key}={value}")
                
                # 生成哈希键
                query_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 执行查询
            result = await query_manager.execute_query(
                query_key,
                lambda: func(*args, **kwargs),
                ttl,
                tags
            )
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步查询函数包装器"""
            # 生成缓存键
            if cache_key:
                query_key = cache_key(*args, **kwargs)
            else:
                # 自动生成缓存键
                import hashlib
                key_parts = [func.__name__]
                
                # 处理参数
                for arg in args:
                    key_parts.append(str(arg))
                
                # 处理关键字参数
                for key, value in sorted(kwargs.items()):
                    key_parts.append(f"{key}={value}")
                
                # 生成哈希键
                query_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_result = query_manager._query_cache.get(query_key)
            if cached_result is not None:
                return cached_result
            
            # 执行查询
            result = func(*args, **kwargs)
            
            # 缓存结果
            query_manager._query_cache.set(query_key, result, tags)
            return result
        
        return wrapper if hasattr(func, "__await__") else sync_wrapper
    
    return decorator


# 批量查询装饰器
def batch_query(concurrency_limit: int = 5):
    """批量查询装饰器
    
    示例用法：
    @batch_query(concurrency_limit=5)
    async def get_multiple_users(user_ids):
        # 批量获取多个用户信息
        queries = []
        for user_id in user_ids:
            queries.append({
                'query_key': f"user:{user_id}",
                'query_func': lambda uid=user_id: db.query(User).filter(User.id == uid).first()
            })
        return await query_manager.execute_batch_queries(queries)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 临时设置并发限制
            original_limit = query_manager._concurrency_limit
            query_manager.set_concurrency_limit(concurrency_limit)
            
            try:
                return await func(*args, **kwargs)
            finally:
                # 恢复原始并发限制
                query_manager.set_concurrency_limit(original_limit)
        
        return wrapper
    
    return decorator


# 导出所有内容
__all__ = [
    "QueryCache",
    "QueryManager",
    "query_manager",
    "optimized_query",
    "batch_query"
]
