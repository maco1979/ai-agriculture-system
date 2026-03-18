# AI农业智能决策系统控制器技能

## 概述

这是一个 WorkBuddy 技能，用于控制本地运行的 AI 农业智能决策系统。

## 安装

将本目录复制到 WorkBuddy 的 skills 目录：

```bash
# 通常位于 ~/.claude/skills/ 或项目目录下的 .claude/skills/
cp -r ai-agriculture-controller ~/.claude/skills/
```

## 要求

- Python 3.8+
- AI农业系统后端运行在 `http://localhost:8001`

## 使用方法

### 通过 WorkBuddy 调用

在 WorkBuddy 中输入：

```
检查AI农业系统状态
```

或：

```
列出所有AI模型
```

### 通过 CLI 直接调用

```bash
# 查看系统状态
python scripts/ai-agriculture-cli.py status

# 列出模型
python scripts/ai-agriculture-cli.py models

# 查看智能体记忆
python scripts/ai-agriculture-cli.py memory

# 查看农业配置
python scripts/ai-agriculture-cli.py agriculture

# 查看系统监控
python scripts/ai-agriculture-cli.py monitor

# 控制摄像头
python scripts/ai-agriculture-cli.py camera open
python scripts/ai-agriculture-cli.py camera close

# PTZ云台控制
python scripts/ai-agriculture-cli.py ptz up
python scripts/ai-agriculture-cli.py ptz down
python scripts/ai-agriculture-cli.py ptz left
python scripts/ai-agriculture-cli.py ptz right
```

## 文件结构

```
ai-agriculture-controller/
├── SKILL.md                    # 技能主文档
├── README.md                   # 本文件
├── scripts/
│   └── ai-agriculture-cli.py  # CLI控制脚本
└── references/
    └── api-reference.md       # API参考文档
```

## 支持的命令

| 命令 | 功能 |
|------|------|
| `status` | 查看系统整体状态 |
| `models` | 列出所有AI模型 |
| `model <id>` | 查看模型详情 |
| `train <id>` | 启动模型训练 |
| `agriculture` | 查看农业决策配置 |
| `memory` | 查看智能体记忆 |
| `memory-add` | 模拟添加记忆 |
| `monitor` | 查看系统监控 |
| `camera <action>` | 摄像头控制 |
| `ptz <direction>` | PTZ云台控制 |

## 故障排除

### 服务未运行

如果提示连接失败，先启动后端服务：

```bash
cd d:/1.6/1.5/backend
python simple_api.py
```

### 端口冲突

确保端口 8001 未被占用：

```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001
```

## 项目信息

- **项目名称**: AI农业智能决策系统
- **项目路径**: d:/1.6/1.5
- **后端地址**: http://localhost:8001
- **前端地址**: http://localhost:3000
