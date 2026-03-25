# 本地部署指南

## 快速开始（推荐）

双击根目录的 **`start-local.bat`** — 它会自动完成所有操作并打开浏览器。

---

## 手动启动（两个终端）

### 终端 1 — 后端

```powershell
cd backend

# 安装精简依赖（首次，约 30 秒）
pip install fastapi "uvicorn[standard]" pydantic python-dotenv loguru httpx requests pyjwt bcrypt cryptography

# 启动（本地精简模式，无需 JAX/GPU/硬件）
python start_simple.py
```

后端启动后访问：
- **API 文档**：http://localhost:8001/docs
- **健康检查**：http://localhost:8001/health

---

### 终端 2 — 前端

```powershell
cd frontend

# 安装依赖（首次，约 1-2 分钟）
npm install

# 启动开发服务器
npm run dev
```

前端启动后访问：**http://localhost:3000**

---

## 端口说明

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 React | http://localhost:3000 | Vite 开发服务器 |
| 后端 FastAPI | http://localhost:8001 | API + Swagger 文档 |
| API 代理 | /api → :8001 | Vite 自动代理，前端直接用 `/api/xxx` |

---

## 本地模式说明

`start_simple.py` 是专为本地开发设计的精简启动器：

| 功能 | 状态 | 原因 |
|------|------|------|
| FastAPI 路由 / REST API | ✅ 正常 | 核心功能 |
| 用户认证 (JWT) | ✅ 正常 | 轻量依赖 |
| 农业数据 API | ✅ 正常（Mock 数据） | — |
| JAX / Flax AI 模型 | 🔶 Mock | 需要 GPU + 大量显存 |
| 区块链 (Hyperledger) | 🔶 禁用 | 需要 Docker + Fabric 网络 |
| 摄像头 PTZ 控制 | 🔶 禁用 | 需要物理设备 |
| Ollama 本地大模型 | 🔶 可选 | 需要单独安装 ollama |

---

## 常见问题

### 前端报错：`Cannot connect to backend`
后端还没启动，等 `start_simple.py` 出现 `Uvicorn running on http://0.0.0.0:8001` 再刷新页面。

### 端口被占用
```powershell
# 查看占用 3000 端口的进程
netstat -ano | findstr :3000

# 查看占用 8001 端口的进程
netstat -ano | findstr :8001

# 根据 PID 强制关闭
taskkill /F /PID <进程ID>
```

### 前端 npm install 超时
```powershell
# 换淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### `ModuleNotFoundError: No module named 'fastapi'`
```powershell
pip install fastapi "uvicorn[standard]"
```

---

## 接入 Ollama 本地大模型（可选）

如果已安装 [Ollama](https://ollama.ai)，后端 `.env` 中的模型配置会自动生效：

```bash
# 拉取模型（选择一个）
ollama pull qwen2.5:14b      # 推荐，中文强
ollama pull deepseek-r1:7b   # 推理模型，较小

# 启动后端（会自动检测 ollama）
python start_simple.py
```

---

## Docker 全量启动（可选）

如果需要完整功能（含 PostgreSQL / Redis）：

```powershell
docker-compose up -d
```

访问 http://localhost（Nginx 反代，自动路由前后端）。
