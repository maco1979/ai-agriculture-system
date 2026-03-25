# 🚀 AI农业决策系统 - 自动化部署指南

## 架构概览

```
GitHub Push → GitHub Actions → 构建 Docker 镜像 → 推送阿里云/腾讯云镜像仓库 → SSH 部署到 ECS
```

---

## 📋 前置条件

| 要求 | 说明 |
|------|------|
| 云服务器 | 阿里云/腾讯云 ECS，建议 2核4G 以上 |
| 操作系统 | Ubuntu 20.04/22.04（推荐）|
| 开放端口 | 80（前端）、8000（后端 API）|
| 镜像仓库 | 阿里云容器镜像服务（ACR）或腾讯云 TCR |
| GitHub Secrets | 见下方配置清单 |

---

## 🔑 第一步：配置 GitHub Secrets

进入 GitHub 仓库 → **Settings → Secrets and variables → Actions → New repository secret**

### 必须配置

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `DEPLOY_SERVER_HOST` | 云服务器公网 IP | `47.100.xxx.xxx` |
| `DEPLOY_SERVER_USER` | SSH 登录用户名 | `root` 或 `ubuntu` |
| `DEPLOY_SERVER_SSH_KEY` | SSH 私钥（完整内容）| `-----BEGIN RSA...` |
| `ALIYUN_REGISTRY_USERNAME` | 阿里云镜像仓库账号 | 你的阿里云账号 |
| `ALIYUN_REGISTRY_PASSWORD` | 阿里云镜像仓库密码 | 访问凭证密码 |

### 可选配置

| Secret 名称 | 说明 |
|------------|------|
| `DEPLOY_SERVER_PORT` | SSH 端口（默认 22）|
| `DINGTALK_WEBHOOK` | 钉钉机器人通知 |

### 如何生成 SSH 密钥对

```bash
# 在本地生成密钥对
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/deploy_key

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/deploy_key.pub root@YOUR_SERVER_IP
# 或手动追加：cat deploy_key.pub >> ~/.ssh/authorized_keys

# 将私钥内容复制到 GitHub Secret（DEPLOY_SERVER_SSH_KEY）
cat ~/.ssh/deploy_key
```

---

## 🏗️ 第二步：修改 CI/CD 配置文件

编辑 `.github/workflows/deploy.yml`，修改以下两处：

```yaml
env:
  REGISTRY: registry.cn-hangzhou.aliyuncs.com   # ← 改为你的区域
  IMAGE_NAMESPACE: your-namespace               # ← 改为你的命名空间
```

**阿里云镜像仓库地址格式：**
- 华东1（杭州）：`registry.cn-hangzhou.aliyuncs.com`
- 华北2（北京）：`registry.cn-beijing.aliyuncs.com`
- 华南1（深圳）：`registry.cn-shenzhen.aliyuncs.com`

**腾讯云改为：**
```yaml
REGISTRY: ccr.ccs.tencentyun.com
```

---

## 🛠️ 第三步：服务器首次配置

```bash
# 1. 连接到服务器
ssh root@YOUR_SERVER_IP

# 2. 创建部署目录
mkdir -p /opt/ai-agriculture
cd /opt/ai-agriculture

# 3. 复制环境变量文件
cp .env.example .env
nano .env   # 填入真实值

# 4. 首次手动部署（之后 push 到 main 自动触发）
bash deploy.sh
```

---

## ⚙️ 第四步：配置 .env 文件

关键变量说明：

```bash
# 数据库（如用云数据库 RDS，填入连接串）
DATABASE_URL=postgresql://user:password@rds-host:5432/ai_agriculture

# JWT 密钥（必须是随机强密码）
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 跨域（改为你的真实域名）
ALLOWED_ORIGINS=https://your-domain.com
```

---

## 🔄 日常操作

### 自动部署（推荐）
```bash
# 在本地修改代码后：
git add .
git commit -m "feat: 你的功能描述"
git push origin main   # ← 推送后自动触发 CI/CD
```

### 手动部署（服务器上）
```bash
cd /opt/ai-agriculture
docker compose pull
docker compose up -d
```

### 查看部署状态
```bash
# 查看所有容器状态
docker compose ps

# 查看后端日志（实时）
docker compose logs -f backend

# 查看前端日志
docker compose logs -f frontend

# 查看最近50行错误
docker compose logs --tail=50 backend | grep -i error
```

### 回滚到上一版本
```bash
cd /opt/ai-agriculture
# 查看历史镜像
docker images | grep ai-agri-backend

# 指定版本标签启动（替换 abc1234 为对应的 git sha）
docker run -d --name ai-agri-backend-old \
  registry.cn-hangzhou.aliyuncs.com/your-namespace/ai-agri-backend:abc1234
```

---

## 🐛 常见问题排查

### 问题1：服务起不来（端口问题）
```bash
# 检查端口占用
netstat -tlnp | grep -E "80|8000"

# 检查容器内端口
docker inspect ai-agri-backend | grep -A 10 "Ports"
```

### 问题2：Flax/JAX 兼容性报错
已通过 `backend/main.py` 的猴子补丁修复，如仍报错：
```bash
# 检查 Python 版本（必须是 3.11）
docker exec ai-agri-backend python --version
```

### 问题3：数据库连接失败
```bash
# 测试数据库连接
docker exec ai-agri-backend python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
engine.connect()
print('数据库连接成功')
"
```

### 问题4：前端无法访问 API
检查 `frontend/nginx.conf` 中 `proxy_pass` 地址是否为 `http://backend:8000`（容器网络内服务名）

---

## 📊 监控

访问以下端点检查系统状态：

| 端点 | 说明 |
|------|------|
| `GET /health` | 后端健康检查 |
| `GET /docs` | FastAPI 交互文档 |
| `GET /redoc` | FastAPI ReDoc 文档 |
| `GET /nginx-health` | 前端 Nginx 健康检查 |

---

## 🔒 安全清单

- [ ] `.env` 已加入 `.gitignore`
- [ ] GitHub Secrets 已正确配置（不要在代码里硬编码密钥）
- [ ] 服务器 SSH 密码登录已禁用（仅密钥登录）
- [ ] 微信小程序 AppID 已替换为占位符（见 `project.config.json.example`）
- [ ] 生产环境 `DEBUG=false`
- [ ] `ALLOWED_ORIGINS` 已限制为真实域名

---

**⚙️ 部署有问题？** 查看 GitHub Actions 的 run 日志，或执行 `docker compose logs -f` 在服务器上查看实时日志。
