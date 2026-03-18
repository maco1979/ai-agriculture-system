"""
异步任务管理器模块
提供并发任务管理和执行功能
"""

import asyncio
import uuid
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

class AsyncTask:
    """异步任务类"""
    
    def __init__(self, task_id: str, func: Callable, *args, **kwargs):
        """初始化异步任务
        
        Args:
            task_id: 任务ID
            func: 任务函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.task: Optional[asyncio.Task] = None
        self.status = "pending"
        self.result: Optional[Any] = None
        self.error: Optional[Exception] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.progress = 0.0
        self.stage = "初始化"
    
    async def run(self):
        """运行任务"""
        self.status = "running"
        self.start_time = datetime.now()
        
        try:
            self.result = await self.func(*self.args, **self.kwargs)
            self.status = "completed"
        except Exception as e:
            self.error = e
            self.status = "failed"
        finally:
            self.end_time = datetime.now()
    
    def cancel(self):
        """取消任务"""
        if self.task and not self.task.done():
            self.task.cancel()
            self.status = "cancelled"
    
    def get_info(self) -> Dict[str, Any]:
        """获取任务信息
        
        Returns:
            任务信息
        """
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "stage": self.stage,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result if self.status == "completed" else None,
            "error": str(self.error) if self.error else None
        }

class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        """初始化任务管理器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, AsyncTask] = {}
        self.pending_tasks: List[AsyncTask] = []
        self.running_tasks_count = 0
        self.task_lock = asyncio.Lock()
    
    async def create_task(self, func: Callable, *args, **kwargs) -> str:
        """创建并提交任务
        
        Args:
            func: 任务函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task = AsyncTask(task_id, func, *args, **kwargs)
        
        async with self.task_lock:
            self.tasks[task_id] = task
            self.pending_tasks.append(task)
        
        # 尝试运行任务
        await self._process_pending_tasks()
        
        return task_id
    
    async def _process_pending_tasks(self):
        """处理待执行任务"""
        async with self.task_lock:
            while self.running_tasks_count < self.max_concurrent_tasks and self.pending_tasks:
                task = self.pending_tasks.pop(0)
                self.running_tasks_count += 1
                
                # 创建并启动任务
                task.task = asyncio.create_task(self._run_task_with_cleanup(task))
    
    async def _run_task_with_cleanup(self, task: AsyncTask):
        """运行任务并清理"""
        try:
            await task.run()
        finally:
            async with self.task_lock:
                self.running_tasks_count -= 1
                # 处理下一批任务
                await self._process_pending_tasks()
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        async with self.task_lock:
            if task_id not in self.tasks:
                return None
            return self.tasks[task_id].get_info()
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        async with self.task_lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.cancel()
            
            # 如果任务在待执行队列中，从队列中移除
            if task in self.pending_tasks:
                self.pending_tasks.remove(task)
                self.running_tasks_count -= 1
            
            return True
    
    async def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出任务
        
        Args:
            status: 任务状态过滤
            
        Returns:
            任务列表
        """
        async with self.task_lock:
            tasks = list(self.tasks.values())
            if status:
                tasks = [task for task in tasks if task.status == status]
            return [task.get_info() for task in tasks]
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        async with self.task_lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            if task.status != "completed":
                return None
            
            return task.result
    
    async def cleanup_completed_tasks(self, max_age: int = 3600):
        """清理已完成的任务
        
        Args:
            max_age: 任务最大保留时间（秒）
        """
        async with self.task_lock:
            current_time = datetime.now()
            tasks_to_remove = []
            
            for task_id, task in self.tasks.items():
                if task.status in ["completed", "failed", "cancelled"]:
                    if task.end_time:
                        age = (current_time - task.end_time).total_seconds()
                        if age > max_age:
                            tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取任务管理器统计信息
        
        Returns:
            统计信息
        """
        status_counts = {}
        for task in self.tasks.values():
            status = task.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": self.running_tasks_count,
            "pending_tasks": len(self.pending_tasks),
            "status_counts": status_counts,
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    def update_task_progress(self, task_id: str, progress: float, stage: str):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度（0-100）
            stage: 阶段信息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress = progress
            task.stage = stage

# 创建全局任务管理器实例
task_manager = AsyncTaskManager(max_concurrent_tasks=5)
