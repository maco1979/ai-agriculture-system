# 🌾 AI农业决策系统 - 部署指南

> **当前策略**：本地运行 + Cloudflare Tunnel 公网穿透（免费）
> GitHub Actions 仅做 CI 验证（代码质量 + Docker 构建），不负责远程部署。

---

## 🚀 快速开始（3步搞定）

### 第1步：确认 Docker 已安装

Windows 用户：安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

验证安装：
```powershell
docker --version
docker compose version
```

### 第2步：一键启动（Windows）

```powershell
# 在项目根目录执行
.\start-local.ps1
```

服务启动后访问：
- 🌐 **前端界面**：http://localhost:3000
- 🔧 **后端 API**：http://localhost:8000
- 📖 **API 文档**：http://localhost:8000/docs

### 第3步：开启公网访问（Cloudflare Tunnel）

```powershell
# 启动服务 + 自动开启 Cloudflare Tunnel
.\start-local.ps1 -Tunnel
```

运行后会输出类似这样的临时公网 URL：
```
Your quick Tunnel has been created! Visit it at:
https://abc123.trycloudflare.com  ← 这就是你的公网地址
```

将这个 URL 分享给任何人，他们就能访问你的系统。

---

## 📋 常用命令

```powershell
# 启动服务
.\start-local.ps1

# 启动 + 开公网穿透
.\start-local.ps1 -Tunnel

# 停止所有服务
.\start-local.ps1 -Stop

# 查看实时日志
.\start-local.ps1 -Logs

# 代码更新后重新构建
.\start-local.ps1 -Rebuild
```

---

## 🌐 Cloudflare Tunnel 详细说明

### 临时 URL（免注册）

每次运行都会生成新的 URL，重启后失效。适合演示、临时分享。

```powershell
# 手动启动前端穿透
cloudflared tunnel --url http://localhost:3000

# 手动启动后端穿透
cloudflared tunnel --url http://localhost:8000
```

### 固定域名（需要注册 Cloudflare 账号）

如果你有域名或需要固定 URL：

1. 注册 [Cloudflare 账号](https://dash.cloudflare.com/sign-up)（免费）
2. 安装 cloudflared：
   ```powershell
   winget install Cloudflare.cloudflared
   ```
3. 登录：
   ```powershell
   cloudflared tunnel login
   ```
4. 创建 Tunnel：
   ```powershell
   cloudflared tunnel create ai-agriculture
   ```
5. 创建配置文件 `cloudflare-tunnel.yml`：
   ```yaml
   tunnel: <你的-tunnel-id>
   credentials-file: C:\Users\你的用户名\.cloudflared\<tunnel-id>.json
   
   ingress:
     - hostname: agri.yourdomain.com    # 你的域名
       service: http://localhost:3000
     - hostname: api.agri.yourdomain.com
       service: http://localhost:8000
     - service: http_status:404
   ```
6. 启动：
   ```powershell
   cloudflared tunnel run ai-agriculture
   ```

---

## 🐳 Docker 服务说明

### 服务组成

| 服务 | 端口 | 说明 |
|------|------|------|
| `backend` | 8000 | FastAPI 后端，含 AI 模型 |
| `frontend` | 3000 | React + Vite 前端（Nginx）|
| `redis` | 6379 | 缓存和会话存储 |

### 首次启动时间

- 首次构建：**5-15 分钟**（需要下载基础镜像 + 安装 Python 依赖）
- 后续启动：**30-60 秒**（镜像已缓存）
- 后端 AI 模型加载：额外 **1-3 分钟**

### 查看服务状态

```powershell
docker compose ps
docker compose logs backend -f    # 实时查看后端日志
docker compose logs frontend -f   # 实时查看前端日志
```

---

## ⚙️ 环境变量配置

复制 `.env.example` 为 `.env`，按需修改：

```powershell
Copy-Item .env.example .env
notepad .env    # 编辑
```

主要配置项：

```env
# 后端配置
SECRET_KEY=your-secret-key-here        # 必改：JWT 密钥
DEBUG=false

# 数据库（可选，默认用文件存储）
DATABASE_URL=sqlite:///./data/app.db

# Redis
REDIS_URL=redis://redis:6379/0

# AI 模型配置（可选）
AI_MODEL_PATH=./models
```

---

## 🔧 GitHub Actions CI 说明

每次 push 到 `main` 分支，自动触发：

```
push to main
    ↓
质量检查（Python 语法 + 单元测试）
    ↓
前端构建验证（npm build）
    ↓
Docker 镜像构建验证（不推送）
    ↓
CI 报告汇总（在 Actions 页面查看）
```

查看 CI 状态：
```
https://github.com/maco1979/ai-agriculture-system/actions
```

---

## 🛠️ 故障排查

### Docker 启动失败
```powershell
# 查看详细错误
docker compose logs backend

# 重置并重新构建
.\start-local.ps1 -Stop
.\start-local.ps1 -Rebuild
```

### 端口冲突
```powershell
# 查看哪个程序占用了端口
netstat -aon | findstr ":8000"
netstat -aon | findstr ":3000"

# 修改端口：编辑 docker-compose.yml 中的 ports 配置
```

### 前端无法连接后端
检查 `.env` 中的 `VITE_API_URL` 是否为 `http://localhost:8000`

### 内存不足
关闭其他程序，或在 Docker Desktop → Settings → Resources → Memory 增加内存限制（建议 4GB+）

---

## 📁 文件结构

```
./
├── .github/workflows/deploy.yml    # CI 验证流水线
├── backend/
│   ├── Dockerfile                  # 后端镜像
│   └── ...
├── frontend/
│   ├── Dockerfile                  # 前端镜像（多阶段构建）
│   ├── nginx.conf                  # Nginx 配置（SPA + API 代理）
│   └── ...
├── docker-compose.yml              # 服务编排
├── start-local.ps1                 # Windows 一键启动
├── start-local.sh                  # Linux/Mac 一键启动
├── .env.example                    # 环境变量模板
└── DEPLOY.md                       # 本文件
```

---

*部署方式：本地 Docker + Cloudflare Tunnel 免费公网穿透*  
*最后更新：2026-03-25*
