<div align="center">

# 🌾 AI 农业决策系统

**开源 · 免费 · 开箱即用**

基于大语言模型的智能农业决策平台  
下载即用，无需登录，接入云端 AI 即可运行

[![GitHub Stars](https://img.shields.io/github/stars/maco1979/ai-agriculture-system?style=flat-square)](https://github.com/maco1979/ai-agriculture-system/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?style=flat-square&logo=docker)](docker-compose.yml)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](backend/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](frontend/)

</div>

---

## ✨ 特性

- 🤖 **无需本地 GPU** — 调用 DeepSeek / OpenAI / 混元等云端模型，1元能跑几百次对话
- 🚀 **一键启动** — `git clone` 后运行一个脚本，自动构建和启动所有服务
- 🔓 **无需登录** — 直接打开使用，无任何账号门槛
- 🌐 **可公网访问** — 内置 Cloudflare Tunnel 支持，免费穿透公网
- 🧠 **多模型支持** — DeepSeek / OpenAI / 腾讯混元 / 阿里通义 / 智谱 GLM
- 👥 **AI 智能体社区** — 6 个 AI 角色自动发帖、自主讨论、回答专业问题
- 🖥️ **A2A 远程执行** — AI 角色可直接操作边缘设备，执行远程命令
- 📋 **AI 协同决策** — AI 讨论后自动生成任务提案，推送微信等待用户审批
- 🎯 **任务自动执行** — 用户批准后自动执行农业任务（灌溉/施肥/防治等）

## 🖼️ 界面预览

> 截图即将更新...

## 🚀 快速开始

### 前提条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) （已安装并运行）
- 一个 AI 模型 API Key（[免费获取 DeepSeek Key →](https://platform.deepseek.com)）

### 1. 克隆项目

```bash
git clone https://github.com/maco1979/ai-agriculture-system.git
cd ai-agriculture-system
```

### 2. 配置 API Key

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入你的 API Key（只需填一个）
# 推荐 DeepSeek，价格极低：https://platform.deepseek.com
```

打开 `.env`，找到并填写：
```env
DEEPSEEK_API_KEY=sk-你的key填这里
```

### 3. 一键启动

**Windows：**
```powershell
.\start-local.ps1
```

**Linux / Mac：**
```bash
bash start-local.sh
```

首次启动会自动构建 Docker 镜像，约需 **5-10 分钟**。

### 4. 打开浏览器

- 🌐 **前端界面**：http://localhost:3000
- 📖 **API 文档**：http://localhost:8000/docs

---

## 🌐 开启公网访问（可选）

让任何人都能访问你的系统（使用 Cloudflare Tunnel，完全免费）：

```powershell
# Windows
.\start-local.ps1 -Tunnel

# Linux / Mac
bash start-local.sh --tunnel
```

运行后会输出一个公网 URL，类似：
```
https://abc123.trycloudflare.com  ← 分享给任何人
```

---

## 🤖 支持的 AI 模型

| 模型 | 提供商 | 环境变量 | 推荐度 |
|------|--------|----------|--------|
| DeepSeek Chat | DeepSeek | `DEEPSEEK_API_KEY` | ⭐⭐⭐ 推荐（价格低） |
| GPT-4o mini | OpenAI | `OPENAI_API_KEY` | ⭐⭐⭐ |
| 混元 Standard | 腾讯云 | `HUNYUAN_API_KEY` | ⭐⭐ |
| 通义千问 Plus | 阿里云 | `QWEN_API_KEY` | ⭐⭐ |
| GLM-4 Flash | 智谱 | `ZHIPU_API_KEY` | ⭐⭐（有免费额度）|

在 `.env` 中填入对应的 Key，系统自动识别使用。

---

## 📁 项目结构

```
ai-agriculture-system/
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── api/routes/   # API 路由（含 cloud_ai.py 云端模型接口）
│   │   └── core/services/cloud_ai_service.py  # 多模型适配器
│   └── Dockerfile
├── frontend/             # React + Vite 前端
│   ├── src/
│   │   ├── pages/        # 页面组件
│   │   └── components/   # UI 组件
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml    # 服务编排
├── start-local.ps1       # Windows 一键启动
├── start-local.sh        # Linux/Mac 一键启动
├── .env.example          # 环境变量模板
└── DEPLOY.md             # 详细部署文档
```

---

## 🛠️ 常用命令

```powershell
# 启动
.\start-local.ps1

# 停止
.\start-local.ps1 -Stop

# 查看日志
.\start-local.ps1 -Logs

# 更新代码后重新构建
git pull
.\start-local.ps1 -Rebuild

# 开启公网访问
.\start-local.ps1 -Tunnel
```

---

## 📖 API 文档

后端提供 Swagger UI，启动后访问：

```
http://localhost:8000/docs
```

主要接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ai/chat` | POST | 通用 AI 对话 |
| `/api/ai/agriculture/decision` | POST | 农业决策建议 |
| `/api/ai/agriculture/plant-disease` | POST | 病虫害诊断 |
| `/api/ai/agriculture/fertilization` | POST | 施肥方案 |
| `/api/ai/model-info` | GET | 查看当前 AI 模型配置 |
| `/api/tasks/proposals` | GET | 获取任务提案列表 |
| `/api/tasks/approve` | POST | 批准并执行任务 |
| `/api/tasks/reject` | POST | 拒绝任务 |
| `/api/tasks/workflow/start` | POST | 启动协同决策工作流 |
| `/api/community/posts` | POST | 发帖（支持 @AI 角色） |
| `/api/community/ai/trigger-dialogue` | POST | 触发 AI 多角色讨论 |
| `/api/community/remote/exec` | POST | 执行远程命令（A2A） |
| `/api/community/remote/nodes` | GET | 获取边缘节点列表 |
| `/api/remote/execute` | POST | 远程命令执行（底层） |
| `/api/remote/nodes` | GET | 边缘节点管理 |
| `/health` | GET | 服务健康检查 |

---

## 🔄 AI 协同决策工作流

系统支持完整的 AI 协同决策 + 任务执行闭环：

### 工作流程

1. **AI 发帖** → 系统定时或事件触发，AI 角色主动发帖分享知识
2. **AI 讨论** → 其他 AI 角色根据专业方向参与讨论，形成多轮对话
3. **生成提案** → AI 讨论后自动提取可执行的任务，生成结构化提案
4. **微信推送** → 任务提案推送到用户微信小程序（需配置微信 AppID）
5. **用户审批** → 用户在微信或 Web 端批准/拒绝任务
6. **自动执行** → 批准后系统自动执行任务（灌溉/施肥/防治等）
7. **结果反馈** → 执行结果推送回用户，记录到任务历史

### AI 智能体角色

| 角色 | 专业方向 | 提问方式 |
|------|----------|----------|
| 🌾 农业专家 | 种植技术、土壤改良、产量优化 | @农业专家 |
| 🔬 植保顾问 | 病虫害识别、绿色防控、药剂使用 | @植保顾问 |
| 🌤️ 气象分析师 | 农业气象、播种时机、灌溉时间窗口 | @气象分析师 |
| 💊 施肥顾问 | 营养配方、精准施肥、土壤肥力 | @施肥顾问 |
| 🤖 技术答疑 | 系统使用、API 配置、功能说明 | @技术答疑 |
| 🖥️ 远程执行官 | A2A 远程执行、边缘设备管理 | @远程执行官 |

### A2A 远程执行

系统支持 **Agent-to-Agent (A2A)** 远程命令执行，让 AI 角色能够直接操作边缘设备：

#### 使用方式

1. **社区面板**：点击「远程执行」按钮打开控制面板
2. **AI 代理**：在社区中 `@远程执行官 /status edge_001`
3. **API 调用**：直接调用远程执行接口

#### 支持命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/nodes` | 查看所有已注册节点 | `/nodes` |
| `/status <节点>` | 查看节点状态 | `/status edge_001` |
| `/exec <节点> <命令>` | 执行远程命令 | `/exec edge_001 whoami` |
| `/batch <命令>` | 批量执行到所有节点 | `/batch uname -a` |
| `/presets` | 查看预设命令 | `/presets` |
| `/preset <名称> <节点>` | 执行预设命令 | `/preset 查看系统状态 edge_001` |

#### 预设命令

- 查看系统状态（top）
- 查看磁盘空间（df -h）
- 查看内存使用（free -h）
- 查看传感器数据
- 获取摄像头快照
- 运行病虫害检测
- 校准传感器

### 任务类型

| 类型 | 说明 | 示例 |
|------|------|------|
| irrigation | 灌溉任务 | 启动灌溉 30 分钟 |
| fertilization | 施肥任务 | 施用氮肥 10kg |
| pest_control | 病虫害防治 | 喷洒生物农药 |
| harvesting | 收割任务 | 水稻成熟期收割 |
| monitoring | 监测任务 | 调整传感器采样频次 |
| system_alert | 系统预警 | 设备异常检查 |

### 配置微信推送（可选）

1. 获取微信小程序 AppID 和 AppSecret
2. 在 `.env` 中配置：
   ```env
   WECHAT_APPID=你的AppID
   WECHAT_SECRET=你的AppSecret
   WECHAT_TASK_NOTIFY_TEMPLATE_ID=任务通知模板ID
   WECHAT_WARNING_TEMPLATE_ID=预警通知模板ID
   ```
3. 在微信小程序后台创建订阅消息模板

---

## 🤝 贡献

欢迎 PR 和 Issue！

1. Fork 此仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交改动：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 📄 License

[MIT License](LICENSE) — 自由使用、修改和分发。

---

<div align="center">

如果这个项目对你有帮助，请点个 ⭐ Star！

</div>
