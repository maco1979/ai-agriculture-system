"""
异步存储工具模块
提供异步的文件操作和数据存储功能
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class AsyncStorage:
    """异步存储类"""
    
    def __init__(self, base_path: str = "./storage"):
        """初始化异步存储
        
        Args:
            base_path: 存储基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)
        self.file_locks: Dict[str, asyncio.Lock] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, float] = {}
        self.default_ttl = 300  # 默认缓存过期时间（秒）
    
    async def _get_lock(self, file_path: str) -> asyncio.Lock:
        """获取文件锁
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件锁
        """
        if file_path not in self.file_locks:
            self.file_locks[file_path] = asyncio.Lock()
        return self.file_locks[file_path]
    
    async def read_json(self, file_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """异步读取JSON文件
        
        Args:
            file_name: 文件名
            use_cache: 是否使用缓存
            
        Returns:
            JSON数据
        """
        file_path = str(self.base_path / file_name)
        
        # 检查缓存
        if use_cache and file_name in self.cache:
            # 检查缓存是否过期
            if file_name not in self.cache_ttl or (asyncio.get_event_loop().time() - self.cache_ttl[file_name]) < self.default_ttl:
                return self.cache[file_name]
        
        async with await self._get_lock(file_path):
            try:
                if not os.path.exists(file_path):
                    return None
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新缓存
                if use_cache:
                    self.cache[file_name] = data
                    self.cache_ttl[file_name] = asyncio.get_event_loop().time()
                
                return data
            except Exception as e:
                print(f"读取文件失败: {file_path}, 错误: {e}")
                return None
    
    async def write_json(self, file_name: str, data: Dict[str, Any]) -> bool:
        """异步写入JSON文件
        
        Args:
            file_name: 文件名
            data: JSON数据
            
        Returns:
            是否成功
        """
        file_path = str(self.base_path / file_name)
        
        async with await self._get_lock(file_path):
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # 更新缓存
                self.cache[file_name] = data
                self.cache_ttl[file_name] = asyncio.get_event_loop().time()
                
                return True
            except Exception as e:
                print(f"写入文件失败: {file_path}, 错误: {e}")
                return False
    
    async def delete_file(self, file_name: str) -> bool:
        """异步删除文件
        
        Args:
            file_name: 文件名
            
        Returns:
            是否成功
        """
        file_path = str(self.base_path / file_name)
        
        async with await self._get_lock(file_path):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # 从缓存中删除
                if file_name in self.cache:
                    del self.cache[file_name]
                if file_name in self.cache_ttl:
                    del self.cache_ttl[file_name]
                
                return True
            except Exception as e:
                print(f"删除文件失败: {file_path}, 错误: {e}")
                return False
    
    async def exists(self, file_name: str) -> bool:
        """异步检查文件是否存在
        
        Args:
            file_name: 文件名
            
        Returns:
            是否存在
        """
        file_path = str(self.base_path / file_name)
        return os.path.exists(file_path)
    
    async def list_files(self, pattern: str = "*") -> list[str]:
        """异步列出文件
        
        Args:
            pattern: 文件模式
            
        Returns:
            文件列表
        """
        import glob
        search_path = str(self.base_path / pattern)
        return glob.glob(search_path)
    
    def clear_cache(self, file_name: Optional[str] = None):
        """清除缓存
        
        Args:
            file_name: 文件名，None表示清除所有缓存
        """
        if file_name:
            if file_name in self.cache:
                del self.cache[file_name]
            if file_name in self.cache_ttl:
                del self.cache_ttl[file_name]
        else:
            self.cache.clear()
            self.cache_ttl.clear()
    
    def set_cache_ttl(self, ttl: float):
        """设置缓存过期时间
        
        Args:
            ttl: 过期时间（秒）
        """
        self.default_ttl = ttl

# 创建全局存储实例
metadata_storage = AsyncStorage("./models")
