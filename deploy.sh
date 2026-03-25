#!/bin/bash
# ============================================================
# AI农业决策系统 - 服务器一键部署脚本
# 在云服务器上首次运行：bash deploy.sh
# ============================================================

set -euo pipefail

# ── 颜色输出 ──────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error()   { echo -e "${RED}[❌]${NC} $1"; exit 1; }

# ── 配置区（请修改以下变量）──────────────────
APP_DIR="/opt/ai-agriculture"
REPO_URL="https://github.com/maco1979/ai-agriculture-system.git"
BRANCH="main"

# ── 检查 Docker 是否安装 ─────────────────────
check_docker() {
  log_info "检查 Docker 环境..."
  if ! command -v docker &> /dev/null; then
    log_warn "Docker 未安装，正在自动安装..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log_success "Docker 安装完成"
  else
    log_success "Docker 已安装：$(docker --version)"
  fi

  if ! docker compose version &> /dev/null; then
    log_warn "Docker Compose Plugin 未安装，正在安装..."
    apt-get update -qq && apt-get install -y docker-compose-plugin
    log_success "Docker Compose 安装完成"
  else
    log_success "Docker Compose 已安装：$(docker compose version)"
  fi
}

# ── 初始化部署目录 ────────────────────────────
setup_directory() {
  log_info "初始化部署目录：$APP_DIR"
  mkdir -p "$APP_DIR"
  cd "$APP_DIR"

  # 创建 .env 文件（如果不存在）
  if [ ! -f ".env" ]; then
    log_warn ".env 文件不存在，请配置环境变量！"
    if [ -f ".env.example" ]; then
      cp .env.example .env
      log_warn "已从 .env.example 复制，请编辑 $APP_DIR/.env 填入真实值"
      echo ""
      echo "  必须配置的变量："
      echo "  - DATABASE_URL"
      echo "  - JWT_SECRET"
      echo "  - ALLOWED_ORIGINS"
      echo ""
      read -p "按回车继续（确认已配置 .env）..." || true
    else
      log_error "找不到 .env.example，请手动创建 .env 文件"
    fi
  fi
}

# ── 拉取最新代码 ─────────────────────────────
pull_code() {
  log_info "拉取最新代码..."
  if [ -d ".git" ]; then
    git fetch origin
    git reset --hard "origin/$BRANCH"
    log_success "代码更新完成"
  else
    git clone --branch "$BRANCH" "$REPO_URL" .
    log_success "代码克隆完成"
  fi
}

# ── 停止旧容器 ────────────────────────────────
stop_old() {
  log_info "停止旧版本容器..."
  docker compose down --remove-orphans 2>/dev/null || true
  log_success "旧容器已停止"
}

# ── 构建并启动 ────────────────────────────────
build_and_start() {
  log_info "构建镜像中（这可能需要几分钟）..."
  docker compose build --no-cache --parallel
  log_success "镜像构建完成"

  log_info "启动所有服务..."
  docker compose up -d
  log_success "服务已启动"
}

# ── 等待服务就绪 ─────────────────────────────
wait_for_health() {
  log_info "等待服务健康检查通过..."
  local max_wait=90
  local elapsed=0

  while [ $elapsed -lt $max_wait ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
      log_success "后端服务健康！"
      break
    fi
    echo -n "."
    sleep 5
    elapsed=$((elapsed + 5))
  done

  if [ $elapsed -ge $max_wait ]; then
    log_warn "后端健康检查超时，请查看日志："
    docker compose logs backend --tail=50
  fi

  if curl -sf http://localhost:80/ > /dev/null 2>&1; then
    log_success "前端服务正常！"
  else
    log_warn "前端暂未响应，请检查：docker compose logs frontend"
  fi
}

# ── 清理旧镜像 ────────────────────────────────
cleanup() {
  log_info "清理未使用的旧镜像..."
  docker image prune -f
  log_success "清理完成"
}

# ── 显示状态 ─────────────────────────────────
show_status() {
  echo ""
  echo "======================================================"
  log_success "🎉 部署完成！"
  echo "======================================================"
  docker compose ps
  echo ""
  echo "📍 访问地址："
  echo "   前端: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP')"
  echo "   后端 API: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):8000"
  echo "   API 文档: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_SERVER_IP'):8000/docs"
  echo ""
  echo "📋 常用命令："
  echo "   查看日志:  docker compose logs -f"
  echo "   重启服务:  docker compose restart"
  echo "   停止服务:  docker compose down"
  echo "   更新部署:  cd $APP_DIR && git pull && docker compose up -d --build"
  echo "======================================================"
}

# ── 主流程 ────────────────────────────────────
main() {
  echo "======================================================"
  echo "  🌾 AI农业决策系统 - 一键部署脚本"
  echo "  时间：$(date '+%Y-%m-%d %H:%M:%S')"
  echo "======================================================"
  echo ""

  check_docker
  setup_directory
  # pull_code     # 如果用 GitHub Actions 推镜像，注释掉这行
  build_and_start
  wait_for_health
  cleanup
  show_status
}

main "$@"
