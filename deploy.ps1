# ============================================
# AI农业决策系统 - PowerShell部署脚本
# ============================================

Write-Host "🚀 开始部署AI农业决策系统..." -ForegroundColor Green

# 函数：打印带颜色的消息
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 检查必要工具
function Check-Dependencies {
    Write-Info "检查依赖工具..."
    
    # 检查Docker
    try {
        $dockerVersion = docker --version
        Write-Info "Docker已安装: $dockerVersion"
    } catch {
        Write-Error "Docker未安装，请先安装Docker Desktop"
        exit 1
    }
    
    # 检查Docker Compose
    try {
        $dockerComposeVersion = docker-compose --version
        Write-Info "Docker Compose已安装: $dockerComposeVersion"
        $DOCKER_COMPOSE = "docker-compose"
    } catch {
        try {
            $dockerComposeVersion = docker compose version
            Write-Info "Docker Compose (新版本)已安装"
            $DOCKER_COMPOSE = "docker compose"
        } catch {
            Write-Error "Docker Compose不可用"
            exit 1
        }
    }
    
    # 检查Azure CLI
    try {
        $azVersion = az --version
        Write-Info "Azure CLI已安装"
        $AZURE_AVAILABLE = $true
    } catch {
        Write-Warning "Azure CLI未安装，跳过Azure部署"
        $AZURE_AVAILABLE = $false
    }
    
    Write-Info "依赖检查完成"
    return @{
        DockerCompose = $DOCKER_COMPOSE
        AzureAvailable = $AZURE_AVAILABLE
    }
}

# 构建Docker镜像
function Build-Images {
    Write-Info "构建Docker镜像..."
    
    # 构建后端镜像
    Write-Info "构建后端镜像..."
    Set-Location "backend"
    docker build -t ai-agriculture-backend:latest .
    Set-Location ".."
    
    # 构建前端镜像
    Write-Info "构建前端镜像..."
    Set-Location "frontend"
    docker build -t ai-agriculture-frontend:latest .
    Set-Location ".."
    
    Write-Info "Docker镜像构建完成"
}

# 本地测试运行
function Run-LocalTest {
    param($DockerCompose)
    
    Write-Info "启动本地测试环境..."
    
    Invoke-Expression "$DockerCompose up -d"
    
    # 等待服务启动
    Start-Sleep -Seconds 10
    
    # 检查服务状态
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
        Write-Info "后端服务运行正常"
    } catch {
        Write-Error "后端服务启动失败"
        Invoke-Expression "$DockerCompose logs backend"
        exit 1
    }
    
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://localhost:80" -UseBasicParsing -ErrorAction Stop
        Write-Info "前端服务运行正常"
    } catch {
        Write-Error "前端服务启动失败"
        Invoke-Expression "$DockerCompose logs frontend"
        exit 1
    }
    
    Write-Info "本地测试环境启动成功" -ForegroundColor Green
    Write-Host "🌐 前端访问: http://localhost" -ForegroundColor Cyan
    Write-Host "🔧 后端API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
}

# Azure部署
function Deploy-ToAzure {
    if (-not $AZURE_AVAILABLE) {
        Write-Warning "Azure CLI不可用，跳过Azure部署"
        return
    }
    
    Write-Info "开始Azure部署..."
    
    # 检查Azure登录状态
    try {
        $account = az account show | ConvertFrom-Json
        Write-Info "已登录Azure账户: $($account.user.name)"
    } catch {
        Write-Info "请登录Azure账户..."
        az login
    }
    
    # 设置订阅
    Write-Info "设置Azure订阅..."
    $subscriptionId = az account show --query id -o tsv
    Write-Info "使用订阅: $subscriptionId"
    
    # 检查AZD
    try {
        $azdVersion = azd --version
        Write-Info "Azure Developer CLI已安装"
    } catch {
        Write-Warning "AZD未安装，请先安装: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd"
        Write-Host "跳过Azure部署" -ForegroundColor Yellow
        return
    }
    
    # 提示用户配置环境变量
    Write-Warning "请配置以下环境变量："
    Write-Host "1. DATABASE_URL: Supabase PostgreSQL连接字符串" -ForegroundColor Yellow
    Write-Host "2. JWT_SECRET_KEY: 生成强随机密钥" -ForegroundColor Yellow
    Write-Host "3. AZURE_STORAGE_CONNECTION_STRING: Azure存储连接字符串" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "是否继续部署？(y/n)"
    if ($confirm -notmatch "^[Yy]$") {
        Write-Info "部署已取消"
        return
    }
    
    # 执行部署
    Write-Info "执行部署..."
    azd up
    
    Write-Info "Azure部署完成" -ForegroundColor Green
}

# 显示部署信息
function Show-DeploymentInfo {
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "✅ 部署完成！" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 部署选项：" -ForegroundColor Yellow
    Write-Host "1. 本地运行: docker-compose up -d" -ForegroundColor White
    Write-Host "2. Azure部署: 已配置基础设施代码" -ForegroundColor White
    Write-Host "3. 手动部署: 参考 DEPLOYMENT_AND_OPERATIONS_GUIDE.md" -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 重要文件：" -ForegroundColor Yellow
    Write-Host "- azure.yaml: Azure部署配置" -ForegroundColor White
    Write-Host "- infra/: Bicep基础设施代码" -ForegroundColor White
    Write-Host "- .env.production: 生产环境配置模板" -ForegroundColor White
    Write-Host "- DEPLOYMENT_AND_OPERATIONS_GUIDE.md: 完整部署指南" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 下一步：" -ForegroundColor Yellow
    Write-Host "1. 配置Supabase数据库" -ForegroundColor White
    Write-Host "2. 更新环境变量" -ForegroundColor White
    Write-Host "3. 执行 azd up 部署到Azure" -ForegroundColor White
    Write-Host "4. 开始用户增长运营" -ForegroundColor White
    Write-Host ""
}

# 主函数
function Main {
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "AI农业决策系统部署脚本" -ForegroundColor Cyan
    Write-Host "===========================================" -ForegroundColor Cyan
    
    # 检查依赖
    $deps = Check-Dependencies
    $DOCKER_COMPOSE = $deps.DockerCompose
    $AZURE_AVAILABLE = $deps.AzureAvailable
    
    # 询问部署选项
    Write-Host ""
    Write-Host "请选择部署选项：" -ForegroundColor Yellow
    Write-Host "1. 构建Docker镜像" -ForegroundColor White
    Write-Host "2. 本地测试运行" -ForegroundColor White
    Write-Host "3. Azure部署" -ForegroundColor White
    Write-Host "4. 全部执行" -ForegroundColor White
    Write-Host "5. 退出" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "请输入选项 (1-5)"
    
    switch ($choice) {
        "1" {
            Build-Images
        }
        "2" {
            Run-LocalTest -DockerCompose $DOCKER_COMPOSE
        }
        "3" {
            Deploy-ToAzure
        }
        "4" {
            Build-Images
            Run-LocalTest -DockerCompose $DOCKER_COMPOSE
            Deploy-ToAzure
        }
        "5" {
            Write-Info "退出部署脚本"
            exit 0
        }
        default {
            Write-Error "无效选项"
            exit 1
        }
    }
    
    Show-DeploymentInfo
}

# 执行主函数
Main