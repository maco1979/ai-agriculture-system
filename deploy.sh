#!/bin/bash

# ============================================
# AI农业决策系统 - 一键部署脚本
# ============================================

set -e  # 遇到错误时退出

echo "🚀 开始部署AI农业决策系统..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要工具
check_dependencies() {
    print_info "检查依赖工具..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "Docker Compose未安装，尝试使用docker compose"
        if ! docker compose version &> /dev/null; then
            print_error "Docker Compose不可用"
            exit 1
        fi
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    # 检查Azure CLI
    if ! command -v az &> /dev/null; then
        print_warning "Azure CLI未安装，跳过Azure部署"
        AZURE_AVAILABLE=false
    else
        AZURE_AVAILABLE=true
    fi
    
    print_info "依赖检查完成"
}

# 构建Docker镜像
build_images() {
    print_info "构建Docker镜像..."
    
    # 构建后端镜像
    print_info "构建后端镜像..."
    cd backend
    docker build -t ai-agriculture-backend:latest .
    cd ..
    
    # 构建前端镜像
    print_info "构建前端镜像..."
    cd frontend
    docker build -t ai-agriculture-frontend:latest .
    cd ..
    
    print_info "Docker镜像构建完成"
}

# 本地测试运行
run_local_test() {
    print_info "启动本地测试环境..."
    
    $DOCKER_COMPOSE up -d
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_info "后端服务运行正常"
    else
        print_error "后端服务启动失败"
        $DOCKER_COMPOSE logs backend
        exit 1
    fi
    
    if curl -f http://localhost:80 > /dev/null 2>&1; then
        print_info "前端服务运行正常"
    else
        print_error "前端服务启动失败"
        $DOCKER_COMPOSE logs frontend
        exit 1
    fi
    
    print_info "本地测试环境启动成功"
    echo "🌐 前端访问: http://localhost"
    echo "🔧 后端API: http://localhost:8000"
    echo "📚 API文档: http://localhost:8000/docs"
}

# Azure部署
deploy_to_azure() {
    if [ "$AZURE_AVAILABLE" = false ]; then
        print_warning "Azure CLI不可用，跳过Azure部署"
        return
    fi
    
    print_info "开始Azure部署..."
    
    # 检查Azure登录状态
    if ! az account show &> /dev/null; then
        print_info "请登录Azure账户..."
        az login
    fi
    
    # 设置订阅
    print_info "设置Azure订阅..."
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    print_info "使用订阅: $SUBSCRIPTION_ID"
    
    # 初始化AZD
    print_info "初始化Azure Developer CLI..."
    if ! command -v azd &> /dev/null; then
        print_warning "AZD未安装，请先安装: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd"
        return
    fi
    
    # 提示用户配置环境变量
    print_warning "请配置以下环境变量："
    echo "1. DATABASE_URL: Supabase PostgreSQL连接字符串"
    echo "2. JWT_SECRET_KEY: 生成强随机密钥"
    echo "3. AZURE_STORAGE_CONNECTION_STRING: Azure存储连接字符串"
    echo ""
    read -p "是否继续部署？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "部署已取消"
        return
    fi
    
    # 执行部署
    print_info "执行部署..."
    azd up
    
    print_info "Azure部署完成"
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "==========================================="
    echo "✅ 部署完成！"
    echo "==========================================="
    echo ""
    echo "📋 部署选项："
    echo "1. 本地运行: docker-compose up -d"
    echo "2. Azure部署: 已配置基础设施代码"
    echo "3. 手动部署: 参考 DEPLOYMENT_AND_OPERATIONS_GUIDE.md"
    echo ""
    echo "🔗 重要文件："
    echo "- azure.yaml: Azure部署配置"
    echo "- infra/: Bicep基础设施代码"
    echo "- .env.production: 生产环境配置模板"
    echo "- DEPLOYMENT_AND_OPERATIONS_GUIDE.md: 完整部署指南"
    echo ""
    echo "🚀 下一步："
    echo "1. 配置Supabase数据库"
    echo "2. 更新环境变量"
    echo "3. 执行 azd up 部署到Azure"
    echo "4. 开始用户增长运营"
    echo ""
}

# 主函数
main() {
    echo "==========================================="
    echo "AI农业决策系统部署脚本"
    echo "==========================================="
    
    # 检查依赖
    check_dependencies
    
    # 询问部署选项
    echo ""
    echo "请选择部署选项："
    echo "1. 构建Docker镜像"
    echo "2. 本地测试运行"
    echo "3. Azure部署"
    echo "4. 全部执行"
    echo "5. 退出"
    echo ""
    
    read -p "请输入选项 (1-5): " choice
    
    case $choice in
        1)
            build_images
            ;;
        2)
            run_local_test
            ;;
        3)
            deploy_to_azure
            ;;
        4)
            build_images
            run_local_test
            deploy_to_azure
            ;;
        5)
            print_info "退出部署脚本"
            exit 0
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
    
    show_deployment_info
}

# 执行主函数
main