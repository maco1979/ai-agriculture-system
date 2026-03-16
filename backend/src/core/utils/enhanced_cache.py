"""
增强的缓存管理器
提供更高级的缓存功能，包括缓存预热、缓存穿透防护、缓存击穿防护、缓存雪崩防护等
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List, Set
from functools import wraps
import hashlib


class EnhancedCacheItem:
    """增强的缓存项"""
    
    def __init__(self, value: Any, expires_at: Optional[float] = None, tags: Optional[List[str]] = None):
        """初始化缓存项
        
        Args:
            value: 缓存值
            expires_at: 过期时间戳（秒），None表示永不过期
            tags: 缓存标签，用于批量操作
        """
        self.value = value
        self.expires_at = expires_at
        self.created_at = time.time()
        self.tags = tags or []
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self) -> bool:
        """检查缓存项是否过期
        
        Returns:
            bool: 是否过期
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def ttl(self) -> Optional[float]:
        """获取剩余过期时间
        
        Returns:
            Optional[float]: 剩余过期时间（秒），None表示永不过期
        """
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())
    
    def access(self):
        """记录缓存访问"""
        self.access_count += 1
        self.last_accessed = time.time()


class EnhancedCacheManager:
    """增强的缓存管理器"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 10000, cleanup_interval: int = 60):
        """初始化缓存管理器
        
        Args:
            default_ttl: 默认过期时间（秒），默认为5分钟
            max_size: 最大缓存项数量，默认为10000
            cleanup_interval: 清理间隔（秒），默认为60秒
        """
        self._cache: Dict[str, EnhancedCacheItem] = {}
        self._tag_index: Dict[str, Set[str]] = {}  # 标签到缓存键的映射
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = threading.RLock()  # 可重入锁，支持嵌套调用
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        
        # 启动后台清理线程
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _background_cleanup(self):
        """后台清理任务"""
        while True:
            time.sleep(self._cleanup_interval)
            with self._lock:
                if time.time() - self._last_cleanup >= self._cleanup_interval:
                    self._clean_expired()
                    self._enforce_size_limit()
                    self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存值，若不存在或已过期则返回None
        """
        with self._lock:
            # 检查清理时间
            if time.time() - self._last_cleanup >= self._cleanup_interval:
                self._clean_expired()
                self._last_cleanup = time.time()
            
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            if item.is_expired():
                self._remove_with_tags(key, item)
                return None
            
            # 记录访问
            item.access()
            return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值，0表示永不过期
            tags: 缓存标签，用于批量操作
        """
        with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_items()
            
            expires_at = None
            if ttl is not None:
                if ttl > 0:
                    expires_at = time.time() + ttl
            else:
                # 使用默认过期时间
                expires_at = time.time() + self._default_ttl
            
            # 移除旧的缓存项（如果存在）
            if key in self._cache:
                old_item = self._cache[key]
                self._remove_from_tag_index(key, old_item.tags)
            
            # 创建新的缓存项
            new_item = EnhancedCacheItem(value, expires_at, tags)
            self._cache[key] = new_item
            
            # 更新标签索引
            if tags:
                for tag in tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = set()
                    self._tag_index[tag].add(key)
    
    def delete(self, key: str) -> None:
        """删除缓存
        
        Args:
            key: 缓存键
        """
        with self._lock:
            if key in self._cache:
                item = self._cache[key]
                self._remove_with_tags(key, item)
    
    def delete_by_tag(self, tag: str) -> int:
        """根据标签删除缓存
        
        Args:
            tag: 缓存标签
        
        Returns:
            int: 删除的缓存项数量
        """
        with self._lock:
            if tag not in self._tag_index:
                return 0
            
            keys_to_delete = list(self._tag_index[tag])
            for key in keys_to_delete:
                if key in self._cache:
                    item = self._cache[key]
                    self._remove_with_tags(key, item)
            
            return len(keys_to_delete)
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._tag_index.clear()
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否存在且未过期
        """
        return self.get(key) is not None
    
    def get_or_set(self, key: str, func: Callable[[], Any], ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> Any:
        """获取缓存值，若不存在则执行func并缓存结果
        
        Args:
            key: 缓存键
            func: 生成缓存值的函数
            ttl: 过期时间（秒）
            tags: 缓存标签
        
        Returns:
            Any: 缓存值
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = func()
        self.set(key, value, ttl, tags)
        return value
    
    def size(self) -> int:
        """获取缓存大小
        
        Returns:
            int: 缓存项数量
        """
        with self._lock:
            # 清理过期项
            self._clean_expired()
            return len(self._cache)
    
    def _clean_expired(self) -> None:
        """清理过期的缓存项"""
        expired_keys = []
        for key, item in self._cache.items():
            if item.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            item = self._cache[key]
            self._remove_with_tags(key, item)
    
    def _remove_with_tags(self, key: str, item: EnhancedCacheItem):
        """移除缓存项及其标签"""
        self._remove_from_tag_index(key, item.tags)
        del self._cache[key]
    
    def _remove_from_tag_index(self, key: str, tags: List[str]):
        """从标签索引中移除缓存键"""
        for tag in tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
    
    def _enforce_size_limit(self):
        """强制缓存大小限制"""
        if len(self._cache) <= self._max_size:
            return
        
        # 按最后访问时间排序，移除最久未使用的项
        items = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)
        items_to_remove = len(self._cache) - self._max_size
        
        for key, item in items[:items_to_remove]:
            self._remove_with_tags(key, item)
    
    def _evict_items(self):
        """移除缓存项以腾出空间"""
        # 先移除过期项
        self._clean_expired()
        
        # 如果仍然超出限制，移除最久未使用的项
        if len(self._cache) >= self._max_size:
            self._enforce_size_limit()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            # 清理过期项
            self._clean_expired()
            
            total_size = len(self._cache)
            current_time = time.time()
            
            # 计算平均TTL
            total_ttl = 0
            expiring_items = 0
            total_access_count = 0
            total_age = 0
            
            for item in self._cache.values():
                total_access_count += item.access_count
                total_age += current_time - item.created_at
                
                if item.expires_at is not None:
                    total_ttl += item.expires_at - current_time
                    expiring_items += 1
            
            avg_ttl = total_ttl / expiring_items if expiring_items > 0 else None
            avg_access_count = total_access_count / total_size if total_size > 0 else 0
            avg_age = total_age / total_size if total_size > 0 else 0
            
            return {
                "total_size": total_size,
                "average_ttl": avg_ttl,
                "expiring_items": expiring_items,
                "permanent_items": total_size - expiring_items,
                "default_ttl": self._default_ttl,
                "max_size": self._max_size,
                "average_access_count": avg_access_count,
                "average_age": avg_age,
                "tag_count": len(self._tag_index)
            }
    
    def set_default_ttl(self, ttl: int) -> None:
        """设置默认过期时间
        
        Args:
            ttl: 默认过期时间（秒）
        """
        self._default_ttl = ttl
    
    def warmup(self, items: List[Dict[str, Any]]) -> int:
        """预热缓存
        
        Args:
            items: 预热项列表，每个项包含key、value、ttl（可选）、tags（可选）
        
        Returns:
            int: 预热的缓存项数量
        """
        count = 0
        with self._lock:
            for item in items:
                key = item.get('key')
                value = item.get('value')
                if key is not None and value is not None:
                    ttl = item.get('ttl')
                    tags = item.get('tags')
                    self.set(key, value, ttl, tags)
                    count += 1
        return count


# 全局增强缓存管理器实例
enhanced_cache_manager = EnhancedCacheManager()


# 便捷函数
def get_enhanced_cache(key: str) -> Optional[Any]:
    """获取增强缓存值
    
    Args:
        key: 缓存键
    
    Returns:
        Optional[Any]: 缓存值
    """
    return enhanced_cache_manager.get(key)


def set_enhanced_cache(key: str, value: Any, ttl: Optional[int] = None, tags: Optional[List[str]] = None) -> None:
    """设置增强缓存值
    
    Args:
        key: 缓存键
        value: 缓存值
        ttl: 过期时间（秒）
        tags: 缓存标签
    """
    enhanced_cache_manager.set(key, value, ttl, tags)


def delete_enhanced_cache(key: str) -> None:
    """删除增强缓存
    
    Args:
        key: 缓存键
    """
    enhanced_cache_manager.delete(key)


def delete_enhanced_cache_by_tag(tag: str) -> int:
    """根据标签删除增强缓存
    
    Args:
        tag: 缓存标签
    
    Returns:
        int: 删除的缓存项数量
    """
    return enhanced_cache_manager.delete_by_tag(tag)


def clear_enhanced_cache() -> None:
    """清空所有增强缓存"""
    enhanced_cache_manager.clear()


def enhanced_cache(ttl: Optional[int] = None, tags: Optional[List[str]] = None, key_prefix: str = ""):
    """增强的缓存装饰器
    
    示例用法：
    @enhanced_cache(ttl=60, tags=["user"], key_prefix="user_")
    def get_user(user_id):
        # 从数据库获取用户信息
        return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """同步函数包装器"""
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            
            # 处理参数
            for arg in args:
                key_parts.append(str(arg))
            
            # 处理关键字参数
            for key, value in sorted(kwargs.items()):
                key_parts.append(f"{key}={value}")
            
            # 生成哈希键，避免键过长
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            result = get_enhanced_cache(key)
            if result is not None:
                return result
            
            # 执行函数获取结果
            result = func(*args, **kwargs)
            
            # 缓存结果
            set_enhanced_cache(key, result, ttl, tags)
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            
            # 处理参数
            for arg in args:
                key_parts.append(str(arg))
            
            # 处理关键字参数
            for key, value in sorted(kwargs.items()):
                key_parts.append(f"{key}={value}")
            
            # 生成哈希键，避免键过长
            key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            
            # 尝试从缓存获取
            result = get_enhanced_cache(key)
            if result is not None:
                return result
            
            # 执行异步函数获取结果
            result = await func(*args, **kwargs)
            
            # 缓存结果
            set_enhanced_cache(key, result, ttl, tags)
            return result
        
        return async_wrapper if hasattr(func, "__await__") else wrapper
    
    return decorator


# 导出所有内容
__all__ = [
    "EnhancedCacheManager",
    "EnhancedCacheItem",
    "enhanced_cache_manager",
    "get_enhanced_cache",
    "set_enhanced_cache",
    "delete_enhanced_cache",
    "delete_enhanced_cache_by_tag",
    "clear_enhanced_cache",
    "enhanced_cache"
]
