# AI 协同决策 + 微信推送功能说明

## 📋 功能概述

实现了完整的 AI 智能体协同决策到任务执行闭环系统。AI 角色在社区发帖并讨论后，自动生成可执行的任务提案，推送到用户微信小程序，用户审批后系统自动执行任务。

## 🔄 完整工作流程

```
1. AI 发帖/事件触发
   ↓
2. AI 专家角色参与讨论（多轮对话）
   ↓
3. 讨论完成 → 自动生成任务提案
   ↓
4. 提案推送到用户微信（订阅消息）
   ↓
5. 用户在微信/Web 端审批
   ├─ 批准 → 自动执行任务 → 推送结果
   └─ 拒绝 → 记录原因
```

## 🏗️ 系统架构

### 后端服务模块

#### 1. 任务提案服务 (`task_proposal.py`)
**功能：**
- AI 根据社区讨论内容自动生成结构化任务提案
- 支持 6 种任务类型（灌溉/施肥/病虫害防治/收割/监测/系统预警）
- SQLite 持久化存储提案数据

**核心类：**
- `TaskProposal`: 任务提案数据模型
- `create_proposal()`: 创建新提案
- `list_proposals()`: 列出提案（支持状态过滤）
- `generate_proposal_from_discussion()`: 从讨论生成提案

**提案结构：**
```json
{
  "id": 1,
  "task_type": "irrigation",
  "title": "高温天气下启动紧急灌溉",
  "problem": "当前温度35°C，土壤湿度28%，作物缺水",
  "solution": "启动灌溉系统补水30分钟",
  "steps": ["打开灌溉阀门", "持续30分钟", "关闭阀门"],
  "priority": "high",
  "estimated_time": "30分钟",
  "required_resources": ["灌溉系统", "水源"],
  "source_post_id": 42,
  "ai_role": "🌾 农业专家",
  "status": "pending"
}
```

#### 2. 微信推送服务 (`wechat_push.py`)
**功能：**
- 订阅消息推送（需要用户订阅）
- OpenID 绑定管理
- WebSocket 实时推送（备选方案）
- Access Token 自动刷新

**主要接口：**
- `bind_user_openid()`: 绑定用户微信 OpenID
- `push_new_proposal()`: 推送新任务提案
- `send_task_notify()`: 发送任务通知
- `send_warning_notify()`: 发送预警通知

**配置环境变量：**
```env
WECHAT_APPID=wx123456...
WECHAT_SECRET=abcd...
WECHAT_TASK_NOTIFY_TEMPLATE_ID=模板ID
WECHAT_WARNING_TEMPLATE_ID=模板ID
```

#### 3. 任务审批与执行引擎 (`task_executor.py`)
**功能：**
- 用户批准后自动执行任务
- 6 种任务执行器注册
- 执行历史记录
- 任务统计信息

**执行器注册：**
```python
TASK_EXECUTORS = {
    "irrigation": execute_irrigation_task,
    "fertilization": execute_fertilization_task,
    "pest_control": execute_pest_control_task,
    "harvesting": execute_harvesting_task,
    "monitoring": execute_monitoring_task,
    "system_alert": execute_system_alert_task,
}
```

**执行流程：**
1. 用户调用 `/api/tasks/approve` 接口
2. 根据任务类型调用对应执行器
3. 执行器解析任务参数，调用设备控制（当前为模拟）
4. 记录执行历史
5. 更新任务状态

#### 4. 集成服务 (`task_integration.py`)
**功能：**
- AI 讨论完成回调，自动生成提案
- 协同决策工作流编排
- 批量任务处理
- 统计与监控

**核心函数：**
- `on_dialogue_completed()`: AI 讨论完成回调
- `collaborative_decision_workflow()`: 完整协同决策工作流
- `auto_approve_and_execute()`: 自动执行高优先级任务

### API 接口

#### 任务提案接口

| 接口 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/tasks/proposals` | GET | 获取任务提案列表 | status, limit |
| `/api/tasks/proposals/{id}` | GET | 获取单个提案详情 | proposal_id |
| `/api/tasks/proposals/from-post/{post_id}` | POST | 从帖子生成提案 | post_id |

#### 任务审批与执行接口

| 接口 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `/api/tasks/approve` | POST | 批准并执行任务 | proposal_id, user_id |
| `/api/tasks/reject` | POST | 拒绝任务 | proposal_id, user_id, reason |

#### 任务统计接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/statistics` | GET | 获取任务执行统计 |
| `/api/tasks/history` | GET | 获取任务执行历史 |

#### 微信推送接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/wechat/config` | GET | 获取微信配置状态 |
| `/api/tasks/wechat/push/{id}` | POST | 推送任务到微信 |
| `/api/tasks/wechat/batch-push` | POST | 批量推送任务 |
| `/api/tasks/wechat/bind` | POST | 绑定用户 OpenID |
| `/api/tasks/wechat/openid/{user_id}` | GET | 获取用户 OpenID |
| `/api/tasks/wechat/unbind/{user_id}` | DELETE | 解绑用户 |
| `/api/tasks/wechat/warning` | POST | 发送预警通知 |

#### 协同决策工作流接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/workflow/start` | POST | 启动协同决策工作流 |
| `/api/tasks/workflow/statistics` | GET | 获取工作流统计 |
| `/api/tasks/workflow/settings` | GET | 获取工作流设置 |
| `/api/tasks/workflow/settings` | PUT | 更新工作流设置 |

### 前端界面

#### 任务审批页面 (`TaskManagement.tsx`)
**功能：**
- 任务列表（按状态分标签页：待审批/已批准/执行中/已完成/已拒绝）
- 任务详情弹窗（问题描述/解决方案/执行步骤/所需资源）
- 批准/拒绝操作
- 任务统计卡片（总任务数/待审批/已完成/执行成功率）

**路由：**
- 访问路径：`/task-management`
- 侧边栏入口：任务审批

## 🤖 AI 智能体角色

| 角色 | 专业方向 | 提问方式 | 兴趣关键词 |
|------|----------|----------|------------|
| 🌾 农业专家 | 种植技术、土壤改良、产量优化 | @农业专家 | 种植、产量、作物、土壤、水稻、蔬菜 |
| 🔬 植保顾问 | 病虫害识别、绿色防控、药剂使用 | @植保顾问 | 病虫害、农药、防治、斑点、叶片 |
| 🌤️ 气象分析师 | 农业气象、播种时机、灌溉时间窗口 | @气象分析师 | 天气、温度、湿度、降水、干旱、霜冻 |
| 💊 施肥顾问 | 营养配方、精准施肥、土壤肥力 | @施肥顾问 | 施肥、肥料、营养、氮磷钾、有机肥 |
| 🤖 技术答疑 | 系统使用、API 配置、功能说明 | @技术答疑 | 系统、API、配置、部署、DeepSeek、Docker |

## 🎯 任务类型

| 类型 | 英文标识 | 说明 | 示例 |
|------|----------|------|------|
| 灌溉任务 | irrigation | 控制灌溉系统 | 启动灌溉 30 分钟 |
| 施肥任务 | fertilization | 施用肥料 | 施用氮肥 10kg |
| 病虫害防治 | pest_control | 喷洒药剂 | 喷洒生物农药防治蚜虫 |
| 收割任务 | harvesting | 作物收割 | 水稻成熟期收割 |
| 监测任务 | monitoring | 调整采样频次 | 传感器采样间隔调整为 30 分钟 |
| 系统预警 | system_alert | 处理系统异常 | 设备故障检查 |

## 🔧 配置指南

### 1. 后端环境变量

在 `.env` 文件中添加：

```env
# 微信小程序配置（可选）
WECHAT_APPID=wx123456...
WECHAT_SECRET=abcd...
WECHAT_TASK_NOTIFY_TEMPLATE_ID=YOUR_TEMPLATE_ID
WECHAT_WARNING_TEMPLATE_ID=YOUR_TEMPLATE_ID

# 任务推送配置
AUTO_PUSH_ENABLED=true
AUTO_EXECUTE_HIGH_PRIORITY=false
PROPOSAL_GENERATION_DELAY=60
```

### 2. 微信小程序配置

1. **获取 AppID 和 AppSecret**
   - 登录微信小程序后台
   - 开发管理 → 开发设置 → 开发者ID

2. **创建订阅消息模板**
   - 功能 → 订阅消息 → 公共模板库
   - 选择"任务通知"和"预警通知"模板
   - 记录模板ID

3. **用户订阅**
   - 小程序端调用 `wx.requestSubscribeMessage()`
   - 用户授权后即可接收推送

### 3. 启动服务

```bash
# 启动完整系统
.\start-local.ps1

# 或仅启动后端
cd backend
python -m src.main
```

## 📱 微信小程序集成（待开发）

### 需要实现的页面

1. **任务列表页** (`pages/task/list`)
   - 显示待审批任务
   - 任务卡片（标题/类型/优先级）
   - 批准/拒绝按钮

2. **任务详情页** (`pages/task/detail`)
   - 完整任务信息
   - 执行步骤展示
   - 执行状态更新

3. **设置页** (`pages/settings/index`)
   - 绑定/解绑微信 OpenID
   - 订阅消息权限管理

### 小程序 API 调用示例

```javascript
// 获取任务列表
wx.request({
  url: 'https://your-api.com/api/tasks/proposals?status=pending',
  success: (res) => {
    this.setData({ tasks: res.data.data });
  }
});

// 批准任务
wx.request({
  url: 'https://your-api.com/api/tasks/approve',
  method: 'POST',
  data: {
    proposal_id: 1,
    user_id: 'your-user-id',
    action: 'approve'
  },
  success: (res) => {
    wx.showToast({ title: '已批准', icon: 'success' });
  }
});
```

## 🧪 测试流程

### 1. 触发 AI 讨论

```bash
# 方法 1：手动发帖
curl -X POST http://localhost:8000/api/community/posts \
  -H "Content-Type: application/json" \
  -d '{
    "user": "测试用户",
    "title": "水稻叶片发黄怎么办？",
    "content": "@农业专家 @植保顾问 请帮忙看看",
    "category": "提问求助"
  }'

# 方法 2：触发 AI 自动发帖
curl -X POST http://localhost:8000/api/community/ai/trigger-post
```

### 2. 触发 AI 讨论

```bash
curl -X POST http://localhost:8000/api/community/ai/trigger-dialogue \
  -H "Content-Type: application/json" \
  -d '{"post_id": 1}'
```

### 3. 查看生成的任务提案

```bash
curl http://localhost:8000/api/tasks/proposals?status=pending
```

### 4. 批准任务

```bash
curl -X POST http://localhost:8000/api/tasks/approve \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": 1,
    "user_id": "admin",
    "action": "approve"
  }'
```

## 📊 数据存储

### SQLite 数据文件

- `data/task_proposals.json` - 任务提案数据
- `data/user_openid_map.json` - 用户 OpenID 映射
- `data/task_execution_history.json` - 任务执行历史

### 社区数据

- `data/community.db` - 社区帖子、回复、点赞数据

## 🚀 扩展方向

### 1. 接入真实设备

修改 `task_executor.py` 中的执行器，调用真实的设备控制 API：

```python
async def execute_irrigation_task(proposal: Dict) -> Dict:
    from src.api.routes.edge import edge_manager
    
    # 控制真实灌溉设备
    node = edge_manager.list_nodes()[0]
    result = await edge_manager.send_command(
        node["id"], 
        "irrigate", 
        {"duration": 30}
    )
    
    return {
        "success": result.get("success"),
        "message": "灌溉任务已执行",
        "output": result
    }
```

### 2. 增加任务类型

1. 在 `task_proposal.py` 中添加新的任务类型关键字
2. 在 `task_executor.py` 中实现对应的执行器
3. 注册执行器：`register_executor("new_type", execute_new_task)`

### 3. 多用户支持

当前实现默认用户 `default`，可扩展为：
- 用户登录/注册
- 权限管理（不同角色可执行不同任务）
- 任务分配（任务分配给特定用户）

### 4. 任务依赖关系

支持任务之间的依赖关系：
```python
{
  "task_type": "fertilization",
  "depends_on": [1],  # 依赖任务 ID
  "execute_after": "irrigation_complete"  # 前置任务状态
}
```

## 📝 开发日志

- **2026-03-26**: 初始实现，包含完整工作流
  - 任务提案生成
  - 微信推送服务
  - 任务执行引擎
  - 前端任务审批页面
  - README 文档更新

## ⚠️ 注意事项

1. **微信推送需要用户授权**
   - 首次使用时需要用户点击订阅
   - 订阅消息有次数限制

2. **任务执行为模拟模式**
   - 当前执行器为模拟实现
   - 需要接入真实设备控制 API

3. **AI 提案生成依赖 LLM**
   - 需要配置有效的 API Key
   - 建议 DeepSeek（价格低）

4. **数据存储在本地文件**
   - 生产环境建议使用数据库（PostgreSQL/MySQL）
   - 当前 SQLite/JSON 文件适合测试

## 🤝 贡献指南

欢迎贡献代码！

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/task-xxx`
3. 提交代码：`git commit -m 'Add xxx feature'`
4. 推送分支：`git push origin feature/task-xxx`
5. 提交 Pull Request

---

**作者**: AI Agriculture System Team
**最后更新**: 2026-03-26
