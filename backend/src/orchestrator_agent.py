"""
多智能体协调者 (Orchestrator Agent)
负责统一调度、路由和协调4个核心智能体的协作工作
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(int, Enum):
    CRITICAL = 0   # 立即执行（故障/告警）
    HIGH = 1       # 高优先级（决策请求）
    NORMAL = 2     # 普通任务
    LOW = 3        # 后台任务（报表/同步）


@dataclass
class AgentTask:
    """智能体任务"""
    task_id: str
    agent_name: str
    action: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False
    duration_ms: float = 0.0


class AgentProxy:
    """
    智能体代理 —— 包装真实智能体实例，提供统一调用接口、
    状态跟踪和超时保护。
    """

    def __init__(self, name: str, agent_instance: Any, timeout_seconds: int = 30):
        self.name = name
        self.instance = agent_instance
        self.timeout = timeout_seconds
        self.status = AgentStatus.IDLE
        self.call_count = 0
        self.error_count = 0
        self.last_call_time: Optional[str] = None
        self.last_error: Optional[str] = None

    async def execute(self, action: str, params: Dict[str, Any]) -> Any:
        """执行智能体动作，带超时和错误统计"""
        self.status = AgentStatus.RUNNING
        self.call_count += 1
        self.last_call_time = datetime.now().isoformat()

        try:
            method = getattr(self.instance, action, None)
            if method is None:
                raise AttributeError(f"智能体 '{self.name}' 没有方法 '{action}'")

            if asyncio.iscoroutinefunction(method):
                result = await asyncio.wait_for(method(**params), timeout=self.timeout)
            else:
                result = method(**params)

            self.status = AgentStatus.IDLE
            return result

        except asyncio.TimeoutError:
            self.status = AgentStatus.ERROR
            self.error_count += 1
            self.last_error = f"执行超时 ({self.timeout}s)"
            raise

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.error_count += 1
            self.last_error = str(e)
            raise

    def get_health(self) -> Dict[str, Any]:
        """返回当前健康状态"""
        success_rate = (
            round((self.call_count - self.error_count) / self.call_count, 3)
            if self.call_count > 0 else 1.0
        )
        return {
            "name": self.name,
            "status": self.status.value,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "last_call_time": self.last_call_time,
            "last_error": self.last_error
        }


class OrchestratorAgent:
    """
    多智能体协调者

    职责：
    - 接收上层请求，分析意图，路由到合适的专业智能体
    - 支持并行任务调度（asyncio）
    - 处理智能体间通信与结果聚合
    - 提供统一的健康状态和任务历史查询
    """

    # 意图 -> 智能体路由表
    INTENT_ROUTING = {
        # 用户交互智能体处理
        "greeting":            [("user_interaction_agent", "handle_greeting", TaskPriority.LOW)],
        "help":                [("user_interaction_agent", "get_help_info", TaskPriority.LOW)],
        "unknown":             [("user_interaction_agent", "handle_unknown", TaskPriority.LOW)],

        # 决策引擎处理
        "query_weather":       [("decision_engine_agent", "get_weather_advice", TaskPriority.NORMAL)],
        "query_crop_status":   [("decision_engine_agent", "get_crop_decision", TaskPriority.NORMAL)],
        "fertilization_advice":[("decision_engine_agent", "get_fertilization_plan", TaskPriority.NORMAL)],
        "harvest_planning":    [("decision_engine_agent", "get_harvest_plan", TaskPriority.NORMAL)],

        # 边缘计算智能体处理
        "irrigation_control":  [("edge_computing_agent", "execute_irrigation", TaskPriority.HIGH)],
        "device_control":      [("edge_computing_agent", "control_device", TaskPriority.HIGH)],

        # 病虫害：先决策分析，再记录区块链（并行）
        "pest_detection": [
            ("decision_engine_agent", "analyze_pest_risk", TaskPriority.HIGH),
            ("blockchain_agent", "record_pest_event", TaskPriority.NORMAL),
        ],

        # 区块链处理
        "blockchain_trace":    [("blockchain_agent", "trace_product", TaskPriority.NORMAL)],

        # 数据查询：决策+系统双路
        "data_query": [
            ("decision_engine_agent", "query_data", TaskPriority.NORMAL),
        ],
        "system_status": [
            ("edge_computing_agent", "get_device_status", TaskPriority.NORMAL),
        ],
    }

    def __init__(self):
        self._agents: Dict[str, AgentProxy] = {}
        self._task_history: List[AgentTask] = []
        self._event_hooks: Dict[str, List[Callable]] = {}
        self._initialized = False
        logger.info("OrchestratorAgent 创建完成")

    # ──────────────────────────────────────────────
    #  智能体注册
    # ──────────────────────────────────────────────

    def register_agent(
        self,
        name: str,
        agent_instance: Any,
        timeout_seconds: int = 30
    ) -> None:
        """注册一个智能体到协调者"""
        proxy = AgentProxy(name, agent_instance, timeout_seconds)
        self._agents[name] = proxy
        logger.info(f"✅ 智能体已注册: {name}")

    def unregister_agent(self, name: str) -> None:
        """注销智能体"""
        if name in self._agents:
            del self._agents[name]
            logger.info(f"❌ 智能体已注销: {name}")

    # ──────────────────────────────────────────────
    #  核心调度
    # ──────────────────────────────────────────────

    async def dispatch(
        self,
        intent: str,
        params: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        根据意图将请求调度到对应的智能体

        Args:
            intent: NLP识别出的意图
            params: 请求参数（传感器数据、实体等）
            user_id: 发起请求的用户ID

        Returns:
            聚合后的执行结果
        """
        routes = self.INTENT_ROUTING.get(intent)
        if not routes:
            logger.warning(f"意图 '{intent}' 没有对应的路由配置")
            return {
                "status": "no_route",
                "intent": intent,
                "message": f"意图 '{intent}' 暂无处理路由",
                "timestamp": datetime.now().isoformat()
            }

        # 分离并行任务和串行任务
        # 相同优先级可并行；CRITICAL优先串行
        parallel_tasks = []
        serial_tasks = []
        for agent_name, action, priority in routes:
            task = AgentTask(
                task_id=f"{user_id}_{intent}_{agent_name}_{int(time.time()*1000)}",
                agent_name=agent_name,
                action=action,
                params=params,
                priority=priority
            )
            if priority == TaskPriority.CRITICAL:
                serial_tasks.append(task)
            else:
                parallel_tasks.append(task)

        results = {}

        # 串行执行关键任务
        for task in sorted(serial_tasks, key=lambda t: t.priority.value):
            result = await self._run_task(task)
            results[task.agent_name] = result

        # 并行执行普通任务
        if parallel_tasks:
            coros = [self._run_task(t) for t in parallel_tasks]
            parallel_results = await asyncio.gather(*coros, return_exceptions=True)
            for task, res in zip(parallel_tasks, parallel_results):
                if isinstance(res, Exception):
                    results[task.agent_name] = {"error": str(res)}
                else:
                    results[task.agent_name] = res

        # 记录历史（只保留最近1000条）
        self._task_history.extend(serial_tasks + parallel_tasks)
        if len(self._task_history) > 1000:
            self._task_history = self._task_history[-1000:]

        # 触发事件钩子
        await self._fire_hooks("after_dispatch", {
            "intent": intent,
            "user_id": user_id,
            "results": results
        })

        return {
            "status": "success",
            "intent": intent,
            "user_id": user_id,
            "results": results,
            "agents_called": list(results.keys()),
            "timestamp": datetime.now().isoformat()
        }

    async def _run_task(self, task: AgentTask) -> Any:
        """执行单个任务，记录耗时"""
        proxy = self._agents.get(task.agent_name)
        if proxy is None:
            task.error = f"智能体 '{task.agent_name}' 未注册"
            task.completed = True
            logger.warning(task.error)
            return {"error": task.error, "agent": task.agent_name}

        start = time.monotonic()
        try:
            result = await proxy.execute(task.action, task.params)
            task.result = result
            task.completed = True
            task.duration_ms = round((time.monotonic() - start) * 1000, 2)
            logger.debug(f"任务完成 [{task.task_id}] {task.agent_name}.{task.action} → {task.duration_ms}ms")
            return result
        except Exception as e:
            task.error = str(e)
            task.completed = True
            task.duration_ms = round((time.monotonic() - start) * 1000, 2)
            logger.error(f"任务失败 [{task.task_id}] {task.agent_name}.{task.action}: {e}")
            return {"error": str(e), "agent": task.agent_name}

    # ──────────────────────────────────────────────
    #  高级协作模式
    # ──────────────────────────────────────────────

    async def collaborative_decision(
        self,
        farm_context: Dict[str, Any],
        user_id: str = "system"
    ) -> Dict[str, Any]:
        """
        多智能体协同决策流程：
        1. 边缘智能体采集最新传感器数据
        2. 决策引擎综合分析
        3. 推荐系统生成个性化建议
        4. 区块链记录决策

        Args:
            farm_context: 农场上下文（位置、作物、面积等）
            user_id: 用户ID

        Returns:
            综合决策结果
        """
        pipeline_result = {
            "user_id": user_id,
            "farm_context": farm_context,
            "timestamp": datetime.now().isoformat(),
            "pipeline": []
        }

        # Step 1: 获取实时传感器数据
        step1 = {
            "step": 1,
            "name": "传感器数据采集",
            "agent": "edge_computing_agent"
        }
        sensor_task = AgentTask(
            task_id=f"cd_step1_{user_id}",
            agent_name="edge_computing_agent",
            action="get_latest_sensor_data",
            params={"zone": farm_context.get("zone", "all")},
            priority=TaskPriority.HIGH
        )
        step1["result"] = await self._run_task(sensor_task)
        pipeline_result["pipeline"].append(step1)

        # 合并传感器数据到上下文
        sensor_data = step1["result"] if not isinstance(step1["result"], dict) or "error" not in step1["result"] else {}
        enriched_context = {**farm_context, **(sensor_data if isinstance(sensor_data, dict) else {})}

        # Step 2: 决策分析（并行：天气+作物+病虫害）
        step2 = {
            "step": 2,
            "name": "多维度决策分析",
            "agents": ["decision_engine_agent"]
        }
        decision_task = AgentTask(
            task_id=f"cd_step2_{user_id}",
            agent_name="decision_engine_agent",
            action="make_comprehensive_decision",
            params={"context": enriched_context},
            priority=TaskPriority.HIGH
        )
        step2["result"] = await self._run_task(decision_task)
        pipeline_result["pipeline"].append(step2)

        # Step 3: 个性化推荐
        step3 = {
            "step": 3,
            "name": "个性化推荐生成",
            "agent": "user_interaction_agent"
        }
        rec_task = AgentTask(
            task_id=f"cd_step3_{user_id}",
            agent_name="user_interaction_agent",
            action="generate_recommendations",
            params={"user_id": user_id, "context": enriched_context},
            priority=TaskPriority.NORMAL
        )
        step3["result"] = await self._run_task(rec_task)
        pipeline_result["pipeline"].append(step3)

        # Step 4: 区块链记录（后台异步，不阻塞结果返回）
        asyncio.create_task(
            self._async_blockchain_record(farm_context, step2["result"], user_id)
        )

        pipeline_result["status"] = "completed"
        pipeline_result["summary"] = self._summarize_pipeline(pipeline_result["pipeline"])
        return pipeline_result

    async def _async_blockchain_record(
        self,
        farm_context: Dict,
        decision_result: Any,
        user_id: str
    ) -> None:
        """后台异步区块链记录，不影响主流程"""
        task = AgentTask(
            task_id=f"bc_record_{user_id}_{int(time.time())}",
            agent_name="blockchain_agent",
            action="record_decision",
            params={"farm_context": farm_context, "decision": decision_result, "user_id": user_id},
            priority=TaskPriority.LOW
        )
        result = await self._run_task(task)
        logger.info(f"区块链记录完成: {result}")

    def _summarize_pipeline(self, pipeline: List[Dict]) -> str:
        """生成流水线执行摘要"""
        completed = sum(1 for s in pipeline if "error" not in str(s.get("result", "")))
        return f"共 {len(pipeline)} 步，成功 {completed} 步"

    # ──────────────────────────────────────────────
    #  状态与监控
    # ──────────────────────────────────────────────

    def get_all_agents_health(self) -> Dict[str, Any]:
        """获取所有智能体健康状态"""
        health_data = {}
        for name, proxy in self._agents.items():
            health_data[name] = proxy.get_health()

        total = len(self._agents)
        online = sum(1 for p in self._agents.values() if p.status != AgentStatus.OFFLINE)
        error_agents = [n for n, p in self._agents.items() if p.status == AgentStatus.ERROR]

        return {
            "orchestrator_status": "running",
            "total_agents": total,
            "online_agents": online,
            "error_agents": error_agents,
            "registered_agents": list(self._agents.keys()),
            "agents": health_data,
            "total_tasks": len(self._task_history),
            "timestamp": datetime.now().isoformat()
        }

    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的任务历史"""
        recent = self._task_history[-limit:]
        return [
            {
                "task_id": t.task_id,
                "agent": t.agent_name,
                "action": t.action,
                "priority": t.priority.name,
                "completed": t.completed,
                "error": t.error,
                "duration_ms": t.duration_ms,
                "created_at": t.created_at
            }
            for t in reversed(recent)
        ]

    def get_routing_config(self) -> Dict[str, Any]:
        """返回当前路由配置（供前端/调试使用）"""
        routing = {}
        for intent, routes in self.INTENT_ROUTING.items():
            routing[intent] = [
                {"agent": a, "action": act, "priority": p.name}
                for a, act, p in routes
            ]
        return {"routes": routing, "total_intents": len(routing)}

    # ──────────────────────────────────────────────
    #  事件钩子
    # ──────────────────────────────────────────────

    def on(self, event: str, hook: Callable) -> None:
        """注册事件钩子"""
        if event not in self._event_hooks:
            self._event_hooks[event] = []
        self._event_hooks[event].append(hook)

    async def _fire_hooks(self, event: str, data: Any) -> None:
        """触发事件钩子"""
        for hook in self._event_hooks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(data)
                else:
                    hook(data)
            except Exception as e:
                logger.warning(f"事件钩子执行失败 [{event}]: {e}")


# ──────────────────────────────────────────────────────────────
# 各专业智能体的简化实现（可替换为完整实现）
# ──────────────────────────────────────────────────────────────

class DecisionEngineAgent:
    """决策引擎智能体"""

    def __init__(self):
        from skills.weather_skill import WeatherSkill
        from skills.crop_skill import CropSkill
        from skills.pest_skill import PestSkill
        self.weather = WeatherSkill()
        self.crop = CropSkill()
        self.pest = PestSkill()
        logger.info("DecisionEngineAgent 初始化完成")

    async def get_weather_advice(self, location: str = "北京", **kwargs) -> Dict[str, Any]:
        async with self.weather as w:
            forecast = await w.get_agriculture_weather(location)
        return {"type": "weather_advice", "data": forecast, "agent": "decision_engine"}

    def get_crop_decision(self, crop_name: str = "水稻", planting_date: str = None, **kwargs) -> Dict[str, Any]:
        planting_date = planting_date or "2026-01-01"
        growth = self.crop.calculate_growth_stage(crop_name, planting_date)
        recommendations = self.crop.get_management_recommendations(
            crop_name, growth.get("current_stage", "生长期")
        )
        return {"type": "crop_decision", "growth_info": growth,
                "recommendations": recommendations, "agent": "decision_engine"}

    def analyze_pest_risk(self, crop_name: str = "水稻",
                          weather_data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        weather_data = weather_data or {"temperature": 28, "humidity": 80}
        risk = self.pest.predict_pest_risk(crop_name, weather_data, "分蘖期")
        return {"type": "pest_analysis", "risk": risk, "agent": "decision_engine"}

    def get_fertilization_plan(self, crop_name: str = "水稻",
                               growth_stage: str = "分蘖期", **kwargs) -> Dict[str, Any]:
        recs = self.crop.get_management_recommendations(crop_name, growth_stage)
        return {"type": "fertilization_plan", "recommendations": recs,
                "crop": crop_name, "stage": growth_stage, "agent": "decision_engine"}

    def get_harvest_plan(self, crop_name: str = "水稻", **kwargs) -> Dict[str, Any]:
        crop_info = self.crop.get_crop_info(crop_name)
        return {"type": "harvest_plan", "crop_info": crop_info,
                "indicator": crop_info.get("harvest_indicator", ""), "agent": "decision_engine"}

    async def make_comprehensive_decision(self, context: Dict, **kwargs) -> Dict[str, Any]:
        crop = context.get("crop_name", "水稻")
        location = context.get("location", "北京")
        try:
            async with self.weather as w:
                weather = await w.get_agriculture_weather(location)
        except Exception:
            weather = {}
        risk = self.pest.predict_pest_risk(
            crop,
            context.get("weather_data", {"temperature": 26, "humidity": 75}),
            context.get("growth_stage", "分蘖期")
        )
        return {"type": "comprehensive_decision", "weather": weather,
                "pest_risk": risk, "agent": "decision_engine", "crop": crop}

    def query_data(self, query_type: str = "sensor", **kwargs) -> Dict[str, Any]:
        return {"type": "data_query", "query_type": query_type,
                "message": "请通过数据看板查询详细历史数据", "agent": "decision_engine"}


class BlockchainAgent:
    """区块链智能体"""

    def __init__(self):
        from skills.blockchain_skill import BlockchainSkill
        self.blockchain = BlockchainSkill()
        logger.info("BlockchainAgent 初始化完成")

    def trace_product(self, product_id: str = "", **kwargs) -> Dict[str, Any]:
        result = self.blockchain.trace_product(product_id)
        return {"type": "trace_result", "product_id": product_id,
                "trace": result, "agent": "blockchain"}

    def record_pest_event(self, crop_name: str = "", pest_data: Dict = None, **kwargs) -> Dict[str, Any]:
        # 模拟上链
        return {"type": "blockchain_record", "event": "pest_detection",
                "status": "recorded", "agent": "blockchain",
                "timestamp": datetime.now().isoformat()}

    def record_decision(self, farm_context: Dict = None,
                        decision: Any = None, user_id: str = "", **kwargs) -> Dict[str, Any]:
        return {"type": "blockchain_record", "event": "ai_decision",
                "status": "recorded", "agent": "blockchain",
                "user_id": user_id, "timestamp": datetime.now().isoformat()}


class EdgeComputingAgent:
    """边缘计算智能体"""

    def __init__(self):
        from skills.device_skill import DeviceSkill
        self.device = DeviceSkill()
        logger.info("EdgeComputingAgent 初始化完成")

    async def execute_irrigation(self, zone: str = "zone_a",
                                  duration_min: int = 10, **kwargs) -> Dict[str, Any]:
        result = await self.device.control_device(
            f"valve_{zone}", "open", {"duration_min": duration_min}
        )
        return {"type": "irrigation", "zone": zone,
                "duration_min": duration_min, "result": result, "agent": "edge"}

    async def control_device(self, device_id: str = "", command: str = "status",
                             parameters: Dict = None, **kwargs) -> Dict[str, Any]:
        result = await self.device.control_device(device_id, command, parameters or {})
        return {"type": "device_control", "device_id": device_id,
                "command": command, "result": result, "agent": "edge"}

    async def get_device_status(self, zone: str = "all", **kwargs) -> Dict[str, Any]:
        devices = await self.device.discover_devices(zone)
        return {"type": "device_status", "zone": zone,
                "devices": devices, "count": len(devices), "agent": "edge"}

    async def get_latest_sensor_data(self, zone: str = "all", **kwargs) -> Dict[str, Any]:
        sensor_data = await self.device.read_sensor_data(f"sensor_{zone}_001")
        return {"type": "sensor_data", "zone": zone,
                "data": sensor_data, "agent": "edge",
                "timestamp": datetime.now().isoformat()}


class UserInteractionAgent:
    """用户交互智能体"""

    def __init__(self):
        from skills.nlp_skill import NLPSkill
        from skills.recommendation_skill import RecommendationSkill
        self.nlp = NLPSkill()
        self.recommender = RecommendationSkill()
        logger.info("UserInteractionAgent 初始化完成")

    def handle_greeting(self, user_id: str = "", text: str = "", **kwargs) -> Dict[str, Any]:
        response = self.nlp.generate_response("greeting")
        return {"type": "greeting", "response": response,
                "user_id": user_id, "agent": "user_interaction"}

    def get_help_info(self, **kwargs) -> Dict[str, Any]:
        response = self.nlp.generate_response("help")
        return {"type": "help", "response": response, "agent": "user_interaction"}

    def handle_unknown(self, text: str = "", **kwargs) -> Dict[str, Any]:
        parsed = self.nlp.parse_command(text)
        return {"type": "unknown_intent", "parsed": parsed,
                "response": parsed["suggested_response"], "agent": "user_interaction"}

    def generate_recommendations(self, user_id: str = "",
                                  context: Dict = None, **kwargs) -> Dict[str, Any]:
        context = context or {}
        recs = self.recommender.recommend_actions(user_id, context)
        return {"type": "recommendations", "user_id": user_id,
                "recommendations": recs, "count": len(recs), "agent": "user_interaction"}

    def parse_user_input(self, text: str = "", user_id: str = "", **kwargs) -> Dict[str, Any]:
        result = self.nlp.parse_command(text)
        return {"type": "nlp_parse", "result": result,
                "user_id": user_id, "agent": "user_interaction"}


# ──────────────────────────────────────────────────────────────
# 工厂函数：创建并注册所有智能体
# ──────────────────────────────────────────────────────────────

def create_orchestrator(timeout_seconds: int = 30) -> OrchestratorAgent:
    """
    工厂函数：创建完整的多智能体协调系统

    Returns:
        已注册所有智能体的 OrchestratorAgent 实例
    """
    orchestrator = OrchestratorAgent()
    errors = []

    agents_to_register = [
        ("decision_engine_agent", DecisionEngineAgent),
        ("blockchain_agent", BlockchainAgent),
        ("edge_computing_agent", EdgeComputingAgent),
        ("user_interaction_agent", UserInteractionAgent),
    ]

    for name, AgentClass in agents_to_register:
        try:
            instance = AgentClass()
            orchestrator.register_agent(name, instance, timeout_seconds)
        except Exception as e:
            logger.error(f"智能体 {name} 初始化失败: {e}")
            errors.append({"agent": name, "error": str(e)})

    if errors:
        logger.warning(f"部分智能体初始化失败: {errors}")
    else:
        logger.info("🎉 所有智能体已成功注册到协调者")

    orchestrator._initialized = True
    orchestrator._init_errors = errors
    return orchestrator
