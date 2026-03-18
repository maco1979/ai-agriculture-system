"""
数据库连接池管理
提供高效的数据库连接管理和连接池功能
"""

import logging
from typing import Dict, Any, Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text

from src.core.settings import settings

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """数据库连接池管理器"""
    
    def __init__(self):
        """初始化数据库连接池"""
        self._engine = None
        self._session_factory = None
        self._initialized = False
    
    def initialize(self):
        """初始化数据库连接池"""
        if self._initialized:
            return
        
        try:
            # 创建同步引擎
            self._engine = create_engine(
                settings.DATABASE_URL,
                pool_size=10,  # 连接池大小
                max_overflow=20,  # 最大溢出连接数
                pool_pre_ping=True,  # 连接池预ping
                pool_recycle=3600,  # 连接回收时间（秒）
                echo=False  # 关闭SQL日志
            )
            
            # 创建会话工厂
            self._session_factory = sessionmaker(
                self._engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False
            )
            
            # 测试连接
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"数据库连接测试成功: {result.scalar()}")
            
            self._initialized = True
            logger.info("数据库连接池初始化成功")
            
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            # 不抛出异常，让应用能够继续运行
            self._initialized = False
    
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话"""
        if not self._initialized:
            logger.warning("数据库连接池未初始化，无法获取会话")
            return
        
        with self._session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"数据库操作失败: {e}")
                raise
    
    def execute(self, query: str, params: Dict[str, Any] = None) -> Any:
        """执行SQL查询"""
        if not self._initialized:
            logger.warning("数据库连接池未初始化，无法执行查询")
            return None
        
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result
    
    def close(self):
        """关闭数据库连接池"""
        if self._engine:
            self._engine.dispose()
            logger.info("数据库连接池已关闭")
    
    def is_initialized(self) -> bool:
        """检查连接池是否已初始化"""
        return self._initialized


# 全局数据库连接池实例
db_pool = DatabasePoolManager()


async def get_db():
    """获取数据库会话的依赖函数"""
    for session in db_pool.get_session():
        yield session


async def init_db():
    """初始化数据库"""
    db_pool.initialize()


async def close_db():
    """关闭数据库"""
    db_pool.close()


class DatabaseOperations:
    """数据库操作类"""
    
    @staticmethod
    async def execute_query(query: str, params: Dict[str, Any] = None) -> Any:
        """执行SQL查询"""
        return db_pool.execute(query, params)
    
    @staticmethod
    async def insert(table: str, data: Dict[str, Any]) -> int:
        """插入数据"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f':{key}' for key in data.keys()])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        result = db_pool.execute(query, data)
        return result.scalar() if result else None
    
    @staticmethod
    async def update(table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """更新数据"""
        set_clause = ', '.join([f"{key} = :{key}" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = :{key}_where" for key in where.keys()])
        
        # 准备参数
        params = {**data}
        for key, value in where.items():
            params[f"{key}_where"] = value
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        result = db_pool.execute(query, params)
        return result.rowcount if result else 0
    
    @staticmethod
    async def delete(table: str, where: Dict[str, Any]) -> int:
        """删除数据"""
        where_clause = ' AND '.join([f"{key} = :{key}" for key in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        result = db_pool.execute(query, where)
        return result.rowcount if result else 0
    
    @staticmethod
    async def select(table: str, where: Dict[str, Any] = None, limit: int = None) -> list:
        """查询数据"""
        where_clause = ''
        if where:
            where_conditions = ' AND '.join([f"{key} = :{key}" for key in where.keys()])
            where_clause = f" WHERE {where_conditions}"
        
        limit_clause = f" LIMIT {limit}" if limit else ''
        query = f"SELECT * FROM {table}{where_clause}{limit_clause}"
        
        result = db_pool.execute(query, where or {})
        return result.mappings().all() if result else []


# 导出所有内容
__all__ = [
    "db_pool",
    "get_db",
    "init_db",
    "close_db",
    "DatabaseOperations"
]