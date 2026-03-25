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
| `/health` | GET | 服务健康检查 |

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
