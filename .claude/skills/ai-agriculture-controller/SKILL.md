---
name: ai-agriculture-controller
description: >
  AI农业智能决策系统控制器 - 通过API控制本地运行的AI农业平台。
  支持AI模型管理、农业决策、系统监控、智能体控制、摄像头操作等功能。
  Use when: 用户需要控制AI农业系统、查看模型状态、执行农业决策、
  监控系统状态、管理训练任务、操作摄像头等。
---

# AI农业智能决策系统控制器

## 功能概述

本技能允许 WorkBuddy 通过 REST API 控制本地运行的 AI 农业智能决策系统。

### 支持的操作

| 模块 | 功能 | API端点 |
|------|------|---------|
| **AI模型** | 查看、启动、暂停、训练模型 | `/api/models/*` |
| **农业决策** | 获取光配方、生长预测、种植规划 | `/api/agriculture/*` |
| **系统监控** | CPU/内存/磁盘监控 | `/api/system/*` |
| **智能体** | 查看状态、模拟记忆 | `/api/v1/fine-tune/*` |
| **摄像头** | 开关摄像头、PTZ控制 | `/api/camera/*` |
| **边缘设备** | 查看设备状态 | `/api/edge/*` |
| **区块链** | 查看链状态 | `/api/blockchain/*` |
| **联邦学习** | 查看学习状态 | `/api/federated/*` |

---

## 环境要求

- 后端服务运行在 `http://localhost:8001`
- 前端服务运行在 `http://localhost:3000`（可选）

---

## 使用方法

### 1. 查看系统整体状态

```bash
python scripts/ai-agriculture-cli.py status
```

### 2. 查看AI模型列表

```bash
python scripts/ai-agriculture-cli.py models
```

### 3. 查看特定模型详情

```bash
python scripts/ai-agriculture-cli.py model organic_core_v1
```

### 4. 启动模型训练

```bash
python scripts/ai-agriculture-cli.py train organic_core_v1
```

### 5. 查看农业决策配置

```bash
python scripts/ai-agriculture-cli.py agriculture
```

### 6. 查看智能体记忆

```bash
python scripts/ai-agriculture-cli.py memory
```

### 7. 模拟添加记忆

```bash
python scripts/ai-agriculture-cli.py memory-add
```

### 8. 查看系统监控

```bash
python scripts/ai-agriculture-cli.py monitor
```

### 9. 控制摄像头

```bash
# 打开摄像头
python scripts/ai-agriculture-cli.py camera open

# 关闭摄像头
python scripts/ai-agriculture-cli.py camera close

# 获取图像
python scripts/ai-agriculture-cli.py camera frame
```

### 10. PTZ云台控制

```bash
# 向上
python scripts/ai-agriculture-cli.py ptz up

# 向下
python scripts/ai-agriculture-cli.py ptz down

# 向左
python scripts/ai-agriculture-cli.py ptz left

# 向右
python scripts/ai-agriculture-cli.py ptz right
```

---

## 快速命令参考

| 命令 | 功能 |
|------|------|
| `检查AI农业系统状态` | 查看整体系统状态 |
| `列出所有AI模型` | 显示7个AI模型列表 |
| `查看智能体记忆` | 显示学习记忆 |
| `查看系统监控` | CPU/内存/磁盘状态 |
| `打开摄像头` | 启动摄像头 |
| `控制PTZ向上` | 云台向上转动 |

---

## 故障排除

### 服务未运行

如果提示连接失败，先启动服务：

```bash
# 启动后端
cd d:/1.6/1.5/backend && python simple_api.py

# 启动前端（可选）
cd d:/1.6/1.5/frontend && npm run dev
```

### API返回错误

- 检查后端日志：`d:/1.6/1.5/backend/logs/backend.log`
- 验证健康检查：`curl http://localhost:8001/health`

---

## 项目信息

- **项目名称**: AI农业智能决策系统
- **后端地址**: http://localhost:8001
- **前端地址**: http://localhost:3000
- **API文档**: http://localhost:8001/docs
- **项目路径**: d:/1.6/1.5
