# 火山引擎部署脚本 (PowerShell版本)
# 用于将AI农业平台部署到火山引擎容器服务(VKE)

param(
    [switch]$SkipBuild = $false,
    [switch]$SkipPush = $false,
    [switch]$SkipDeploy = $false
)

# 配置变量
$ErrorActionPreference = "Stop"
$REGISTRY = "cr.volcengine.com/ai-agriculture"
$NAMESPACE = "ai-agriculture"
$VOLCENGINE_USERNAME = "volcen"
$VOLCENGINE_PASSWORD_BASE64 = "WmpJNVl6QXpORGt6TXpoak5HWTJZemt3T1RaaU1HVmxPRFV3WkRZNVlUQQ=="

# 主程序
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI农业平台 - 火山引擎部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 步骤1: 检查必需工具
Write-Host ""
Write-Host "[1/8] 检查必需工具..." -ForegroundColor Yellow

try {
    $dockerVersion = docker --version 2>&1
    Write-Host "[OK] Docker已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 需要Docker但未安装" -ForegroundColor Red
    Write-Host "请访问 https://www.docker.com/products/docker-desktop 下载安装"
    exit 1
}

try {
    $kubectlVersion = kubectl version --client 2>&1
    Write-Host "[OK] kubectl已安装" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 需要kubectl但未安装" -ForegroundColor Red
    Write-Host "安装方法:"
    Write-Host "  1. 使用 Chocolatey: choco install kubernetes-cli"
    Write-Host "  2. 手动下载: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
    exit 1
}

# 步骤2: 登录火山引擎镜像仓库
Write-Host ""
Write-Host "[2/8] 登录火山引擎镜像仓库..." -ForegroundColor Yellow

try {
    $VOLCENGINE_PASSWORD = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($VOLCENGINE_PASSWORD_BASE64))
    
    # 使用环境变量方式登录
    $env:DOCKER_USERNAME = $VOLCENGINE_USERNAME
    $env:DOCKER_PASSWORD = $VOLCENGINE_PASSWORD
    
    # 登录
    $loginOutput = echo $env:DOCKER_PASSWORD | docker login cr.volcengine.com -u $env:DOCKER_USERNAME --password-stdin 2>&1
    
    Write-Host "[OK] 镜像仓库登录成功" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 镜像仓库登录失败: $_" -ForegroundColor Red
    exit 1
}

# 步骤3-6: 构建镜像
if (-not $SkipBuild) {
    # 构建后端核心镜像
    Write-Host ""
    Write-Host "[3/8] 构建后端核心镜像..." -ForegroundColor Yellow
    try {
        if (Test-Path "backend/Dockerfile") {
            Write-Host "正在构建 backend-core 镜像..."
            docker build -t $REGISTRY/backend-core:latest -f backend/Dockerfile backend/
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/backend-core:latest $REGISTRY/backend-core:$timestamp
            Write-Host "[OK] 后端核心镜像构建完成" -ForegroundColor Green
        } else {
            Write-Host "[WARN] 后端Dockerfile不存在，跳过" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] 后端核心镜像构建失败: $_" -ForegroundColor Red
    }

    # 构建API网关镜像
    Write-Host ""
    Write-Host "[4/8] 构建API网关镜像..." -ForegroundColor Yellow
    try {
        if (Test-Path "microservices/api-gateway/Dockerfile") {
            Write-Host "正在构建 api-gateway 镜像..."
            docker build -t $REGISTRY/api-gateway:latest microservices/api-gateway/
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/api-gateway:latest $REGISTRY/api-gateway:$timestamp
            Write-Host "[OK] API网关镜像构建完成" -ForegroundColor Green
        } else {
            Write-Host "[WARN] API网关目录不存在，跳过" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] API网关镜像构建失败: $_" -ForegroundColor Red
    }

    # 构建前端镜像
    Write-Host ""
    Write-Host "[5/8] 构建前端镜像..." -ForegroundColor Yellow
    try {
        if (Test-Path "microservices/frontend-web/Dockerfile") {
            Write-Host "正在构建 frontend-web 镜像..."
            docker build -t $REGISTRY/frontend-web:latest microservices/frontend-web/
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/frontend-web:latest $REGISTRY/frontend-web:$timestamp
            Write-Host "[OK] 前端镜像构建完成" -ForegroundColor Green
        } else {
            Write-Host "[WARN] 前端目录不存在，跳过" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] 前端镜像构建失败: $_" -ForegroundColor Red
    }

    # 构建决策服务镜像
    Write-Host ""
    Write-Host "[6/8] 构建决策服务镜像..." -ForegroundColor Yellow
    try {
        if (Test-Path "decision-service/Dockerfile") {
            Write-Host "正在构建 decision-service 镜像..."
            docker build -t $REGISTRY/decision-service:latest decision-service/
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/decision-service:latest $REGISTRY/decision-service:$timestamp
            Write-Host "[OK] 决策服务镜像构建完成" -ForegroundColor Green
        } else {
            Write-Host "[WARN] 决策服务目录不存在，跳过" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] 决策服务镜像构建失败: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[INFO] 跳过镜像构建" -ForegroundColor Cyan
}

# 步骤7: 推送镜像
if (-not $SkipPush) {
    Write-Host ""
    Write-Host "[7/8] 推送镜像到火山引擎镜像仓库..." -ForegroundColor Yellow
    
    try {
        Write-Host "推送 backend-core..."
        docker push $REGISTRY/backend-core:latest
        Write-Host "[OK] 后端核心镜像推送完成" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] 后端核心镜像推送失败: $_" -ForegroundColor Red
    }

    if (Test-Path "microservices/api-gateway/Dockerfile") {
        try {
            Write-Host "推送 api-gateway..."
            docker push $REGISTRY/api-gateway:latest
            Write-Host "[OK] API网关镜像推送完成" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] API网关镜像推送失败: $_" -ForegroundColor Red
        }
    }

    if (Test-Path "microservices/frontend-web/Dockerfile") {
        try {
            Write-Host "推送 frontend-web..."
            docker push $REGISTRY/frontend-web:latest
            Write-Host "[OK] 前端镜像推送完成" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] 前端镜像推送失败: $_" -ForegroundColor Red
        }
    }

    if (Test-Path "decision-service/Dockerfile") {
        try {
            Write-Host "推送 decision-service..."
            docker push $REGISTRY/decision-service:latest
            Write-Host "[OK] 决策服务镜像推送完成" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] 决策服务镜像推送失败: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[INFO] 跳过镜像推送" -ForegroundColor Cyan
}

# 步骤8: 部署到Kubernetes
if (-not $SkipDeploy) {
    Write-Host ""
    Write-Host "[8/8] 部署到火山引擎Kubernetes集群..." -ForegroundColor Yellow

    # 检查kubectl连接
    try {
        $clusterInfo = kubectl cluster-info 2>&1
        Write-Host "[OK] 已连接到Kubernetes集群" -ForegroundColor Green
        Write-Host "集群信息: $clusterInfo" -ForegroundColor Gray
    } catch {
        Write-Host "[ERROR] 无法连接到Kubernetes集群" -ForegroundColor Red
        Write-Host "请确保:"
        Write-Host "  1. 已配置kubectl访问火山引擎VKE集群"
        Write-Host "  2. 已设置 KUBECONFIG 环境变量"
        Write-Host "  3. 已运行: kubectl config use-context <your-vke-cluster>"
        exit 1
    }

    # 应用部署配置
    Write-Host ""
    Write-Host "应用Kubernetes配置..." -ForegroundColor Cyan
    try {
        kubectl apply -f volcengine-deployment.yaml
        Write-Host "[OK] Kubernetes配置已应用" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Kubernetes配置应用失败: $_" -ForegroundColor Red
        exit 1
    }

    # 等待部署完成
    Write-Host ""
    Write-Host "等待部署完成..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10

    # 检查部署状态
    Write-Host ""
    Write-Host "部署状态检查:" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Pods:" -ForegroundColor Yellow
    kubectl get pods -n $NAMESPACE

    Write-Host ""
    Write-Host "Services:" -ForegroundColor Yellow
    kubectl get services -n $NAMESPACE

    Write-Host ""
    Write-Host "Deployments:" -ForegroundColor Yellow
    kubectl get deployments -n $NAMESPACE

    Write-Host ""
    Write-Host "Ingress:" -ForegroundColor Yellow
    kubectl get ingress -n $NAMESPACE

    # 获取访问地址
    Write-Host ""
    Write-Host "访问地址:" -ForegroundColor Yellow
    try {
        $ingressIp = kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>&1
        if ($ingressIp) {
            Write-Host "  前端地址: http://$ingressIp" -ForegroundColor White
            Write-Host "  API地址: http://$ingressIp/api" -ForegroundColor White
            Write-Host "  文档地址: http://$ingressIp/docs" -ForegroundColor White
        } else {
            Write-Host "[WARN] Ingress IP尚未分配，请稍后检查" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARN] 无法获取Ingress地址: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] 跳过Kubernetes部署" -ForegroundColor Cyan
}

# 完成
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "常用命令:" -ForegroundColor Yellow
Write-Host "  查看Pod日志: kubectl logs -n $NAMESPACE <pod-name>" -ForegroundColor Gray
Write-Host "  进入Pod: kubectl exec -it -n $NAMESPACE <pod-name> -- /bin/sh" -ForegroundColor Gray
Write-Host "  查看所有资源: kubectl get all -n $NAMESPACE" -ForegroundColor Gray
Write-Host "  删除部署: kubectl delete -f volcengine-deployment.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "详细文档请查看: VOLCENGINE_DEPLOY_GUIDE.md" -ForegroundColor Cyan
