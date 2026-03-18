---
name: ai-agriculture-system
description: >
  AI农业决策系统主控技能 - 管理和操控本地运行的智慧农业平台（端口8001）。
  覆盖农业决策、摄像头/PTZ云台控制、AI模型管理、推理服务、区块链溯源、联邦学习、系统监控等全功能。
  同时支持多智能体协同决策流水线：自然语言 → NLP意图识别 → 4智能体并行决策 → 区块链存证 → 结构化建议输出。
  Use when: 用户提到农业、作物、种植、摄像头、AI模型、区块链、系统状态等关键词，
             或明确要求操作"农业系统"/"AI平台"/"这个系统"，
             或说出任何农业相关的自然语言指令（如"水稻需要浇水吗"、"帮我做一个协同决策"）。
  NOT for: 与农业系统无关的通用查询，或后端服务未运行时（先检查服务状态）。
---

# AI 农业决策系统 — OpenClaw 接入指南（v2.0）

## 系统信息

- **后端地址**: `http://localhost:8001`
- **API文档**: `http://localhost:8001/docs`
- **技术栈**: FastAPI + Python，支持模拟模式（无需AI依赖）

---

## 启动检查

在执行任何操作前，先验证服务是否在线：

```bash
curl -s http://localhost:8001/api/system/health
```

若返回 `{"status":"healthy"}` 则服务正常。若服务未启动，告知用户运行：

```bash
cd d:/1.6/1.5/backend && python simple_api.py
```

---

## 能力模块一览

| 模块 | 端点前缀 | 主要功能 |
|------|---------|---------|
| 🌱 农业决策 | `/api/decision/` | 光配方生成、生长预测、种植规划、作物建议 |
| 📷 摄像头控制 | `/api/camera/` | 摄像头开关、PTZ云台方向/变焦/预置位/自动跟踪 |
| 🤖 AI模型管理 | `/api/models/` | 模型列表/启停/训练/推理执行 |
| 📊 系统监控 | `/api/system/` | CPU/内存/磁盘、健康状态、区块链、联邦学习 |
| 🧠 多智能体系统 | `/api/agents/` | NLP解析、协同决策、智能体调度、个性化推荐 |

---

## 通用规则

1. **所有 POST 请求使用 JSON**：`Content-Type: application/json`
2. **错误处理**：HTTP 4xx/5xx 时，向用户解释原因并提供修复建议
3. **模拟模式说明**：若硬件不可用，系统自动降级到模拟模式，功能正常但数据为仿真数据
4. **结果格式**：用清晰的中文摘要呈现 API 返回数据，避免直接粘贴原始 JSON
5. **NLP优先**：当用户说出模糊自然语言时，**优先调用 `/api/agents/nlp/parse` 识别意图**，再按意图路由到对应操作

---

## 多智能体系统（/api/agents/）

### 架构说明

```
用户自然语言
      ↓  (NLP意图识别)
 OrchestratorAgent（协调者）
      ↓  (意图路由)
  ┌───────────────────────────────────┐
  │ DecisionEngineAgent  天气/作物/施肥 │
  │ BlockchainAgent      溯源/存证     │
  │ EdgeComputingAgent   灌溉/设备控制  │
  │ UserInteractionAgent 问候/帮助/推荐 │
  └───────────────────────────────────┘
      ↓  (结果聚合)
   结构化中文决策建议
```

---

### 端点速查表

| 端点 | 方法 | 功能 | 何时使用 |
|------|------|------|---------|
| `/api/agents/health` | GET | 所有智能体健康状态 | "智能体状态怎么样" |
| `/api/agents/skills` | GET | 已注册技能模块列表 | "有哪些技能" |
| `/api/agents/routing` | GET | 意图→智能体路由配置 | "路由是怎么配置的" |
| `/api/agents/tasks` | GET | 最近任务执行历史 | "最近执行了什么任务" |
| `/api/agents/nlp/parse` | POST | 自然语言意图识别 + 实体提取 | 用户说模糊农业指令 |
| `/api/agents/recommend` | POST | 传感器数据 → 个性化行动推荐 | "给我推荐下一步操作" |
| `/api/agents/dispatch` | POST | 按意图直接调度智能体 | 已知意图，直接执行 |
| `/api/agents/collaborative-decision` | POST | **4智能体全流水线协同决策** | "帮我做协同决策" |

---

### 意图路由表（NLP识别后的路由规则）

| 意图标识 | 触发词示例 | 路由到 |
|---------|----------|--------|
| `query_weather` | 天气、气温、预报 | DecisionEngineAgent |
| `query_crop_status` | 作物状态、长势、诊断 | DecisionEngineAgent |
| `fertilization_advice` | 施肥、追肥、氮磷钾 | DecisionEngineAgent |
| `harvest_planning` | 收割、采摘、何时收 | DecisionEngineAgent |
| `irrigation_control` | 灌溉、浇水、供水 | EdgeComputingAgent |
| `device_control` | 开关设备、阀门、泵 | EdgeComputingAgent |
| `pest_detection` | 病虫害、叶片异常、黄叶 | DecisionEngineAgent + BlockchainAgent（并行） |
| `blockchain_trace` | 溯源、区块链、记录 | BlockchainAgent |
| `data_query` | 查数据、历史记录 | DecisionEngineAgent |
| `system_status` | 系统状态、设备状态 | EdgeComputingAgent |
| `greeting` | 你好、帮我、能做什么 | UserInteractionAgent |

---

## 自然语言触发示例

### 场景一：模糊指令 → 自动识别意图

**用户说**：「水稻叶片有点发黄，我该怎么办？」

**你应该**：
1. 调用 NLP 解析，识别意图
2. 根据意图路由到病虫害分析
3. 用中文汇报结果

```bash
# Step 1：NLP 意图识别
curl -s -X POST http://localhost:8001/api/agents/nlp/parse \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"水稻叶片有点发黄，我该怎么办？\", \"user_id\": \"user001\"}"
```

返回示例：
```json
{
  "result": {
    "intent": {"intent": "pest_detection", "confidence": 0.78},
    "entities": ["水稻", "叶片", "发黄"],
    "suggested_reply": "检测到病虫害风险信号，正在分析..."
  }
}
```

```bash
# Step 2：按识别意图调度智能体
curl -s -X POST http://localhost:8001/api/agents/dispatch \
  -H "Content-Type: application/json" \
  -d "{\"intent\": \"pest_detection\", \"params\": {\"crop\": \"水稻\", \"symptom\": \"叶片发黄\"}, \"user_id\": \"user001\"}"
```

---

### 场景二：协同决策（最强模式，触发全流水线）

**用户说**：「帮我对 A 区水稻做一次完整的协同决策」或「启动多智能体决策流水线」

**你应该**：直接调用 collaborative-decision，不需要先做 NLP

```bash
curl -s -X POST http://localhost:8001/api/agents/collaborative-decision \
  -H "Content-Type: application/json" \
  -d "{
    \"crop_name\": \"水稻\",
    \"location\": \"北京\",
    \"zone\": \"zone_a\",
    \"growth_stage\": \"分蘖期\",
    \"user_id\": \"user001\"
  }"
```

**流水线执行步骤**（后端自动完成）：
1. `DecisionEngineAgent` → 获取天气、作物状态、施肥计划
2. `EdgeComputingAgent` → 读取传感器数据（土壤湿度/温度/光照）
3. `UserInteractionAgent` → 调用 RecommendationSkill 生成优先级推荐
4. `BlockchainAgent` → 将决策结果写入区块链存证

**回复用户时**用以下格式汇报：
```
🌾 协同决策完成 — 水稻（分蘖期，zone_a）

📍 决策摘要
• 天气状况：[天气智能体结果]
• 作物诊断：[决策引擎结果]
• 传感器读数：土壤湿度 XX%，温度 XX°C

⚡ 优先行动建议（按紧急度排序）
1. [最高优先级建议]
2. [次优先级建议]
3. [常规建议]

🔗 区块链存证：[交易哈希或记录ID]
⏱ 决策耗时：XX ms
```

---

### 场景三：传感器数据 → 个性化推荐

**用户说**：「根据当前传感器数据给我推荐操作」

```bash
curl -s "http://localhost:8001/api/agents/recommend?\
user_id=user001&\
soil_moisture=22&\
temperature=36&\
humidity=88&\
light_intensity=600&\
ph=6.2&\
days_since_fertilization=15&\
growth_progress=0.4"
```

---

### 场景四：直接调度已知意图

**用户说**：「查一下天气建议」/ 「给出施肥方案」

```bash
# 天气建议
curl -s -X POST http://localhost:8001/api/agents/dispatch \
  -H "Content-Type: application/json" \
  -d "{\"intent\": \"query_weather\", \"params\": {\"location\": \"北京\"}, \"user_id\": \"user001\"}"

# 施肥建议
curl -s -X POST http://localhost:8001/api/agents/dispatch \
  -H "Content-Type: application/json" \
  -d "{\"intent\": \"fertilization_advice\", \"params\": {\"crop\": \"水稻\", \"growth_stage\": \"分蘖期\"}, \"user_id\": \"user001\"}"

# 灌溉控制
curl -s -X POST http://localhost:8001/api/agents/dispatch \
  -H "Content-Type: application/json" \
  -d "{\"intent\": \"irrigation_control\", \"params\": {\"zone\": \"zone_a\", \"duration\": 30}, \"user_id\": \"user001\"}"
```

---

### 场景五：查看智能体状态

**用户说**：「智能体系统状态怎么样」/ 「有哪些技能在运行」

```bash
# 智能体健康状态
curl -s http://localhost:8001/api/agents/health | python -m json.tool

# 技能模块列表
curl -s http://localhost:8001/api/agents/skills | python -m json.tool

# 最近10条任务历史
curl -s "http://localhost:8001/api/agents/tasks?limit=10" | python -m json.tool
```

---

## 传统功能快速操作

### 检查系统整体状态
```bash
curl -s http://localhost:8001/api/system/health | python -m json.tool
```

### 查看所有AI模型
```bash
curl -s http://localhost:8001/api/models | python -m json.tool
```

### 获取农业决策建议（传统端点）
```bash
curl -s -X POST http://localhost:8001/api/decision/agriculture \
  -H "Content-Type: application/json" \
  -d "{\"crop_type\": \"番茄\", \"growth_stage\": \"开花期\", \"environment_data\": {}}"
```

---

## 决策优先级说明

当用户的需求可以通过多个路径处理时，按以下顺序选择：

1. **明确要求协同决策** → 直接调用 `collaborative-decision`（全流水线）
2. **模糊农业自然语言** → 先 `nlp/parse` 识别意图，再 `dispatch` 执行
3. **明确指定某个意图** → 直接 `dispatch`，跳过 NLP
4. **传感器数据推荐** → 调用 `recommend` 端点
5. **传统 API 操作** → 使用 `/api/decision/`、`/api/camera/` 等原有端点

---

## 完整对话示例

```
用户：水稻出现白叶病怎么办，帮我分析一下
你：[调用 nlp/parse] → 意图: pest_detection
    [调用 dispatch(pest_detection)] → 病虫害分析 + 区块链存证
    回复：检测到白叶病风险，建议立即施用苯甲·丙环唑，同时降低田间湿度。
          决策已存证，区块链记录ID: bc_xxx

用户：帮我对B区番茄做一次完整的多智能体协同决策
你：[调用 collaborative-decision] → 全流水线
    回复：🌾 协同决策完成...（按上方格式汇报）

用户：当前土壤湿度是18%，温度39度，我该做什么
你：[调用 recommend(soil_moisture=18, temperature=39...)]
    回复：优先级推荐：1. 立即灌溉（紧急）2. 开启遮阳网（高）3. 检查肥料浓度（普通）

用户：智能体都正常吗
你：[调用 /agents/health]
    回复：4个智能体全部在线，成功率100%。最近任务：协同决策（2ms前）
```
