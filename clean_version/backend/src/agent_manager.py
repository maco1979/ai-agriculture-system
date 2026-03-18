"""
智能体生命周期管理器 (Agent Manager)
负责智能体的初始化、配置加载、健康检查和优雅关闭
"""

import asyncio
import yaml
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# 全局单例协调者
_orchestrator = None
_manager_initialized = False
_init_time: Optional[str] = None


def get_orchestrator():
    """获取全局协调者单例（懒加载）"""
    global _orchestrator, _manager_initialized, _init_time
    if _orchestrator is None:
        logger.info("首次获取协调者，开始初始化多智能体系统...")
        try:
            from src.orchestrator_agent import create_orchestrator
            _orchestrator = create_orchestrator(timeout_seconds=30)
            _manager_initialized = True
            _init_time = datetime.now().isoformat()
            logger.info("✅ 多智能体系统初始化完成")
        except Exception as e:
            logger.error(f"❌ 多智能体系统初始化失败: {e}")
            _manager_initialized = False
            raise
    return _orchestrator


def is_initialized() -> bool:
    return _manager_initialized


def get_init_time() -> Optional[str]:
    return _init_time


def load_agent_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载智能体配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "agent_config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info(f"✅ 配置文件加载成功: {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"配置文件解析失败: {e}")
        return {}


async def health_check_all() -> Dict[str, Any]:
    """对所有智能体执行健康检查"""
    if not is_initialized():
        return {
            "status": "not_initialized",
            "message": "多智能体系统尚未初始化",
            "timestamp": datetime.now().isoformat()
        }

    try:
        orchestrator = get_orchestrator()
        health = orchestrator.get_all_agents_health()
        health["system_initialized"] = True
        health["init_time"] = get_init_time()
        return health
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def dispatch_command(
    intent: str,
    params: Dict[str, Any],
    user_id: str = "api_user"
) -> Dict[str, Any]:
    """统一命令分发入口"""
    try:
        orchestrator = get_orchestrator()
        return await orchestrator.dispatch(intent, params, user_id)
    except Exception as e:
        logger.error(f"命令分发失败 [{intent}]: {e}")
        return {
            "status": "error",
            "intent": intent,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def run_collaborative_decision(
    farm_context: Dict[str, Any],
    user_id: str = "api_user"
) -> Dict[str, Any]:
    """运行多智能体协同决策流水线"""
    try:
        orchestrator = get_orchestrator()
        return await orchestrator.collaborative_decision(farm_context, user_id)
    except Exception as e:
        logger.error(f"协同决策失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
