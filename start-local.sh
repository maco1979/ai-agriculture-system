#!/bin/bash
# ============================================================
# AI农业决策系统 - Linux/Mac 一键本地启动脚本
# 用法：bash start-local.sh [选项]
#   -s | --stop     停止服务
#   -r | --rebuild  重新构建镜像
#   -l | --logs     查看日志
#   -t | --tunnel   启动 Cloudflare Tunnel
# ============================================================

set -e

PROJECT_NAME="ai-agriculture"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; NC='\033[0m'

step()  { echo -e "  ${CYAN}→${NC} $1"; }
ok()    { echo -e "  ${GREEN}✅${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠️${NC}  $1"; }
fail()  { echo -e "  ${RED}❌${NC} $1"; exit 1; }
title() { echo -e "\n${MAGENTA}$1${NC}"; }

# 解析参数
STOP=false; REBUILD=false; LOGS=false; TUNNEL=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stop)    STOP=true    ;;
        -r|--rebuild) REBUILD=true ;;
        -l|--logs)    LOGS=true    ;;
        -t|--tunnel)  TUNNEL=true  ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

title "🌾 AI农业决策系统 - 本地启动器"
echo "  时间：$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd "$SCRIPT_DIR"

# 停止服务
if [ "$STOP" = true ]; then
    step "停止所有服务..."
    docker compose -p $PROJECT_NAME down
    ok "服务已停止"
    exit 0
fi

# 查看日志
if [ "$LOGS" = true ]; then
    docker compose -p $PROJECT_NAME logs -f --tail=100
    exit 0
fi

# ── 检查依赖 ─────────────────────────────────────────
title "📋 检查环境依赖"

command -v docker &>/dev/null || fail "未找到 Docker！请先安装：https://docs.docker.com/get-docker/"
ok "Docker: $(docker --version)"

docker info &>/dev/null || fail "Docker 未运行！请先启动 Docker。"
ok "Docker 运行正常"

# ── .env 文件 ────────────────────────────────────────
title "🔧 环境变量配置"
if [ ! -f ".env" ]; then
    warn ".env 不存在，从模板创建..."
    cp .env.example .env
    ok ".env 已创建，如需修改请编辑此文件"
else
    ok ".env 文件已存在"
fi

# ── 构建和启动 ───────────────────────────────────────
title "🐳 启动 Docker 服务"

if [ "$REBUILD" = true ]; then
    step "重新构建镜像..."
    docker compose -p $PROJECT_NAME build --no-cache
    ok "构建完成"
fi

step "启动服务（首次需要 3-10 分钟）..."
docker compose -p $PROJECT_NAME up -d --build

# ── 等待就绪 ─────────────────────────────────────────
title "⏳ 等待服务启动"
MAX_WAIT=60; ELAPSED=0; BACKEND_OK=false
while [ $ELAPSED -lt $MAX_WAIT ]; do
    sleep 3; ELAPSED=$((ELAPSED + 3))
    if curl -sf http://localhost:8000/health &>/dev/null; then
        BACKEND_OK=true; break
    fi
    echo "  等待后端启动... ($ELAPSED/$MAX_WAIT 秒)"
done

# ── 显示结果 ─────────────────────────────────────────
title "📊 服务状态"
docker compose -p $PROJECT_NAME ps

title "🌐 访问地址"
if [ "$BACKEND_OK" = true ]; then
    ok "后端 API:    http://localhost:8000"
    ok "API 文档:    http://localhost:8000/docs"
    ok "前端界面:    http://localhost:3000"
else
    warn "后端仍在初始化（AI 模型加载中），稍后访问 http://localhost:8000/health"
fi

# ── Cloudflare Tunnel ────────────────────────────────
if [ "$TUNNEL" = true ]; then
    title "🌏 启动 Cloudflare Tunnel"
    
    if ! command -v cloudflared &>/dev/null; then
        warn "未找到 cloudflared，正在安装..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install cloudflared 2>/dev/null || warn "请手动安装：https://github.com/cloudflare/cloudflared/releases"
        else
            # Linux
            wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
                -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared || \
                warn "安装失败，请手动安装"
        fi
    fi
    
    if command -v cloudflared &>/dev/null; then
        step "启动前端 Tunnel（临时公网 URL）..."
        cloudflared tunnel --url http://localhost:3000 &
        TUNNEL_PID=$!
        step "启动后端 Tunnel..."
        cloudflared tunnel --url http://localhost:8000
        wait $TUNNEL_PID
    fi
else
    title "💡 公网访问提示"
    echo -e "  如需公网访问，运行：${CYAN}bash start-local.sh --tunnel${NC}"
    echo -e "  或手动：${CYAN}cloudflared tunnel --url http://localhost:3000${NC}"
fi

title "📌 常用命令"
echo "  停止服务:   bash start-local.sh --stop"
echo "  查看日志:   bash start-local.sh --logs"
echo "  重新构建:   bash start-local.sh --rebuild"
echo "  开启公网:   bash start-local.sh --tunnel"
echo ""
