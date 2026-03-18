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

# 颜色函数
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($message) {
    Write-ColorOutput Green "[✓] $message"
}

function Write-Info($message) {
    Write-ColorOutput Cyan "[i] $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "[!] $message"
}

function Write-Error($message) {
    Write-ColorOutput Red "[✗] $message"
}

function Write-Step($step, $total, $message) {
    Write-Output ""
    Write-ColorOutput Yellow "[$step/$total] $message"
}

# 主程序
Write-Output "========================================"
Write-Output "  AI农业平台 - 火山引擎部署脚本"
Write-Output "========================================"

# 步骤1: 检查必需工具
Write-Step 1 8 "检查必需工具..."

try {
    $dockerVersion = docker --version 2>&1
    Write-Success "Docker已安装: $dockerVersion"
} catch {
    Write-Error "需要Docker但未安装"
    Write-Output "请访问 https://www.docker.com/products/docker-desktop 下载安装"
    exit 1
}

try {
    $kubectlVersion = kubectl version --client 2>&1
    Write-Success "kubectl已安装"
} catch {
    Write-Error "需要kubectl但未安装"
    Write-Output "安装方法:"
    Write-Output "  1. 使用 Chocolatey: choco install kubernetes-cli"
    Write-Output "  2. 手动下载: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/"
    exit 1
}

# 步骤2: 登录火山引擎镜像仓库
Write-Step 2 8 "登录火山引擎镜像仓库..."

try {
    $VOLCENGINE_PASSWORD = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($VOLCENGINE_PASSWORD_BASE64))
    
    # 创建临时文件存储密码
    $tempFile = [System.IO.Path]::GetTempFileName()
    $VOLCENGINE_PASSWORD | Out-File -FilePath $tempFile -Encoding ASCII -NoNewline
    
    # 登录
    $loginOutput = docker login cr.volcengine.com -u $VOLCENGINE_USERNAME --password-stdin < $tempFile 2>&1
    Remove-Item $tempFile
    
    Write-Success "镜像仓库登录成功"
} catch {
    Write-Error "镜像仓库登录失败: $_"
    exit 1
}

# 步骤3-6: 构建镜像
if (-not $SkipBuild) {
    # 构建后端核心镜像
    Write-Step 3 8 "构建后端核心镜像..."
    try {
        if (Test-Path "backend/Dockerfile") {
            docker build -t $REGISTRY/backend-core:latest -f backend/Dockerfile backend/ | Out-String
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/backend-core:latest $REGISTRY/backend-core:$timestamp | Out-Null
            Write-Success "后端核心镜像构建完成"
        } else {
            Write-Warning "后端Dockerfile不存在，跳过"
        }
    } catch {
        Write-Error "后端核心镜像构建失败: $_"
    }

    # 构建API网关镜像
    Write-Step 4 8 "构建API网关镜像..."
    try {
        if (Test-Path "microservices/api-gateway/Dockerfile") {
            docker build -t $REGISTRY/api-gateway:latest microservices/api-gateway/ | Out-String
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/api-gateway:latest $REGISTRY/api-gateway:$timestamp | Out-Null
            Write-Success "API网关镜像构建完成"
        } else {
            Write-Warning "API网关目录不存在，跳过"
        }
    } catch {
        Write-Error "API网关镜像构建失败: $_"
    }

    # 构建前端镜像
    Write-Step 5 8 "构建前端镜像..."
    try {
        if (Test-Path "microservices/frontend-web/Dockerfile") {
            docker build -t $REGISTRY/frontend-web:latest microservices/frontend-web/ | Out-String
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/frontend-web:latest $REGISTRY/frontend-web:$timestamp | Out-Null
            Write-Success "前端镜像构建完成"
        } else {
            Write-Warning "前端目录不存在，跳过"
        }
    } catch {
        Write-Error "前端镜像构建失败: $_"
    }

    # 构建决策服务镜像
    Write-Step 6 8 "构建决策服务镜像..."
    try {
        if (Test-Path "decision-service/Dockerfile") {
            docker build -t $REGISTRY/decision-service:latest decision-service/ | Out-String
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            docker tag $REGISTRY/decision-service:latest $REGISTRY/decision-service:$timestamp | Out-Null
            Write-Success "决策服务镜像构建完成"
        } else {
            Write-Warning "决策服务目录不存在，跳过"
        }
    } catch {
        Write-Error "决策服务镜像构建失败: $_"
    }
} else {
    Write-Info "跳过镜像构建"
}

# 步骤7: 推送镜像
if (-not $SkipPush) {
    Write-Step 7 8 "推送镜像到火山引擎镜像仓库..."
    
    try {
        docker push $REGISTRY/backend-core:latest | Out-String
        Write-Success "后端核心镜像推送完成"
    } catch {
        Write-Error "后端核心镜像推送失败: $_"
    }

    if (Test-Path "microservices/api-gateway/Dockerfile") {
        try {
            docker push $REGISTRY/api-gateway:latest | Out-String
            Write-Success "API网关镜像推送完成"
        } catch {
            Write-Error "API网关镜像推送失败: $_"
        }
    }

    if (Test-Path "microservices/frontend-web/Dockerfile") {
        try {
            docker push $REGISTRY/frontend-web:latest | Out-String
            Write-Success "前端镜像推送完成"
        } catch {
            Write-Error "前端镜像推送失败: $_"
        }
    }

    if (Test-Path "decision-service/Dockerfile") {
        try {
            docker push $REGISTRY/decision-service:latest | Out-String
            Write-Success "决策服务镜像推送完成"
        } catch {
            Write-Error "决策服务镜像推送失败: $_"
        }
    }
} else {
    Write-Info "跳过镜像推送"
}

# 步骤8: 部署到Kubernetes
if (-not $SkipDeploy) {
    Write-Step 8 8 "部署到火山引擎Kubernetes集群..."

    # 检查kubectl连接
    try {
        $clusterInfo = kubectl cluster-info 2>&1
        Write-Success "已连接到Kubernetes集群"
        Write-Info "集群信息: $clusterInfo"
    } catch {
        Write-Error "无法连接到Kubernetes集群"
        Write-Output "请确保:"
        Write-Output "  1. 已配置kubectl访问火山引擎VKE集群"
        Write-Output "  2. 已设置 KUBECONFIG 环境变量"
        Write-Output "  3. 已运行: kubectl config use-context <your-vke-cluster>"
        exit 1
    }

    # 应用部署配置
    Write-Info "应用Kubernetes配置..."
    try {
        kubectl apply -f volcengine-deployment.yaml 2>&1 | Out-String
        Write-Success "Kubernetes配置已应用"
    } catch {
        Write-Error "Kubernetes配置应用失败: $_"
        exit 1
    }

    # 等待部署完成
    Write-Info "等待部署完成..."
    Start-Sleep -Seconds 10

    # 检查部署状态
    Write-Output ""
    Write-ColorOutput Cyan "部署状态检查:"
    
    Write-Output ""
    Write-ColorOutput Yellow "Pods:"
    kubectl get pods -n $NAMESPACE 2>&1

    Write-Output ""
    Write-ColorOutput Yellow "Services:"
    kubectl get services -n $NAMESPACE 2>&1

    Write-Output ""
    Write-ColorOutput Yellow "Deployments:"
    kubectl get deployments -n $NAMESPACE 2>&1

    Write-Output ""
    Write-ColorOutput Yellow "Ingress:"
    kubectl get ingress -n $NAMESPACE 2>&1

    # 获取访问地址
    Write-Output ""
    Write-ColorOutput Yellow "访问地址:"
    try {
        $ingressIp = kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>&1
        if ($ingressIp) {
            Write-Output "  前端地址: http://$ingressIp"
            Write-Output "  API地址: http://$ingressIp/api"
            Write-Output "  文档地址: http://$ingressIp/docs"
        } else {
            Write-Warning "Ingress IP尚未分配，请稍后检查"
        }
    } catch {
        Write-Warning "无法获取Ingress地址: $_"
    }
} else {
    Write-Info "跳过Kubernetes部署"
}

# 完成
Write-Output ""
Write-Output "========================================"
Write-Success "部署完成!"
Write-Output "========================================"
Write-Output ""
Write-ColorOutput Yellow "常用命令:"
Write-Output "  查看Pod日志: kubectl logs -n $NAMESPACE <pod-name>"
Write-Output "  进入Pod: kubectl exec -it -n $NAMESPACE <pod-name> -- /bin/sh"
Write-Output "  查看所有资源: kubectl get all -n $NAMESPACE"
Write-Output "  删除部署: kubectl delete -f volcengine-deployment.yaml"
Write-Output ""
Write-ColorOutput Cyan "详细文档请查看: VOLCENGINE_DEPLOY_GUIDE.md"
