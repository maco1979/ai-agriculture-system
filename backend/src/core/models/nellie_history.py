"""
NELLIE推理历史数据模型
用于存储和管理NELLIE神经符号推理的历史记录
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
import json


@dataclass
class NellieHistoryItem:
    """
    NELLIE推理历史项的数据模型
    """
    id: str
    query: str
    context: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    status: str
    confidence: Optional[float] = None
    reasoning_path: Optional[Any] = None
    timestamp: datetime = None
    processing_time: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[list[str]] = None
    multimodal_inputs: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化默认值"""
        if self.id is None:
            self.id = str(uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.status is None:
            self.status = "completed"
        if self.multimodal_inputs is None:
            self.multimodal_inputs = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NellieHistoryItem':
        """从字典创建实例"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'NellieHistoryItem':
        """从JSON字符串创建实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class NellieHistoryManager:
    """
    NELLIE推理历史管理器
    用于管理和存储NELLIE推理历史记录
    """
    
    def __init__(self):
        """初始化历史管理器"""
        self.history: Dict[str, NellieHistoryItem] = {}
        self.max_history_size = 1000  # 最大历史记录数量
    
    def save_history(self, item: NellieHistoryItem) -> str:
        """
        保存推理历史记录
        
        Args:
            item: 推理历史项
            
        Returns:
            历史记录ID
        """
        # 检查历史记录数量，超过限制则删除最旧的记录
        if len(self.history) >= self.max_history_size:
            # 找到最旧的记录
            oldest_id = min(self.history.keys(), 
                           key=lambda x: self.history[x].timestamp)
            # 删除最旧记录
            del self.history[oldest_id]
        
        # 保存新记录
        self.history[item.id] = item
        return item.id
    
    def get_history(self, history_id: str) -> Optional[NellieHistoryItem]:
        """
        根据ID获取历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录项，如果不存在则返回None
        """
        return self.history.get(history_id)
    
    def get_history_list(self, 
                        limit: int = 50, 
                        offset: int = 0, 
                        sort_by: str = "timestamp",
                        sort_order: str = "desc",
                        filters: Optional[Dict[str, Any]] = None) -> list[NellieHistoryItem]:
        """
        获取历史记录列表
        
        Args:
            limit: 返回记录的最大数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序（asc/desc）
            filters: 过滤条件
            
        Returns:
            历史记录列表
        """
        # 应用过滤条件
        filtered_history = list(self.history.values())
        
        if filters:
            filtered_history = [item for item in filtered_history if 
                              all(self._apply_filter(item, k, v) for k, v in filters.items())]
        
        # 排序
        reverse = sort_order == "desc"
        
        if sort_by == "timestamp":
            filtered_history.sort(key=lambda x: x.timestamp, reverse=reverse)
        elif sort_by == "confidence":
            filtered_history.sort(key=lambda x: x.confidence if x.confidence is not None else -1, reverse=reverse)
        elif sort_by == "processing_time":
            filtered_history.sort(key=lambda x: x.processing_time if x.processing_time is not None else float('inf'), reverse=reverse)
        
        # 分页
        return filtered_history[offset:offset + limit]
    
    def _apply_filter(self, item: NellieHistoryItem, key: str, value: Any) -> bool:
        """
        应用过滤条件
        
        Args:
            item: 历史记录项
            key: 过滤字段
            value: 过滤值
            
        Returns:
            是否符合过滤条件
        """
        if key == "status":
            return item.status == value
        elif key == "user_id":
            return item.user_id == value
        elif key == "session_id":
            return item.session_id == value
        elif key == "tags":
            return value in item.tags
        elif key == "query_contains":
            return value.lower() in item.query.lower()
        elif key == "from_timestamp":
            return item.timestamp >= datetime.fromisoformat(value)
        elif key == "to_timestamp":
            return item.timestamp <= datetime.fromisoformat(value)
        return True
    
    def delete_history(self, history_id: str) -> bool:
        """
        删除历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            删除是否成功
        """
        if history_id in self.history:
            del self.history[history_id]
            return True
        return False
    
    def clear_history(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        清空历史记录
        
        Args:
            filters: 过滤条件，仅删除符合条件的记录
            
        Returns:
            删除的记录数量
        """
        if filters is None:
            count = len(self.history)
            self.history.clear()
            return count
        
        # 应用过滤条件删除
        filtered_ids = [item.id for item in self.history.values() if 
                       all(self._apply_filter(item, k, v) for k, v in filters.items())]
        
        for history_id in filtered_ids:
            del self.history[history_id]
        
        return len(filtered_ids)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取历史记录统计信息
        
        Returns:
            统计信息字典
        """
        total = len(self.history)
        
        # 按状态统计
        status_counts = {}
        for item in self.history.values():
            status_counts[item.status] = status_counts.get(item.status, 0) + 1
        
        # 平均处理时间
        processing_times = [item.processing_time for item in self.history.values() 
                          if item.processing_time is not None]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None
        
        # 平均置信度
        confidences = [item.confidence for item in self.history.values() 
                      if item.confidence is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        return {
            "total": total,
            "status_counts": status_counts,
            "avg_processing_time": avg_processing_time,
            "avg_confidence": avg_confidence,
            "oldest_record": min(self.history.values(), key=lambda x: x.timestamp).timestamp if total > 0 else None,
            "newest_record": max(self.history.values(), key=lambda x: x.timestamp).timestamp if total > 0 else None
        }


# 创建历史管理器实例
nellie_history_manager = NellieHistoryManager()
