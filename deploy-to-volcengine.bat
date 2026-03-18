@echo off
chcp 65001 >nul
echo ========================================
echo   AI农业平台 - 火山引擎部署脚本
echo ========================================
echo.

REM 检查Docker
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker已安装

REM 检查kubectl
where kubectl >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] kubectl未安装
    echo 请先安装kubectl
    pause
    exit /b 1
)
echo [OK] kubectl已安装

REM 检查KubeConfig
if not exist "%USERPROFILE%\.kube\config" (
    echo [ERROR] 未找到KubeConfig文件
    echo 请从火山引擎控制台下载KubeConfig并保存到: %USERPROFILE%\.kube\config
    echo 下载地址: https://console.volcengine.com/vke/cluster
    pause
    exit /b 1
)
echo [OK] KubeConfig已配置

REM 设置环境变量
set KUBECONFIG=%USERPROFILE%\.kube\config

REM 验证kubectl连接
echo.
echo [1/6] 验证Kubernetes连接...
kubectl cluster-info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 无法连接到Kubernetes集群
    echo 请检查KubeConfig配置
    pause
    exit /b 1
)
echo [OK] 已连接到Kubernetes集群

REM 登录镜像仓库
echo.
echo [2/6] 登录火山引擎镜像仓库...
docker login cr.volcengine.com -u volcen -p ZjI5YzAzNDkzMjhkNGY2Y2ZlMjkwOTZiMGVlOTY4YTA
if %errorlevel% neq 0 (
    echo [ERROR] 镜像仓库登录失败
    pause
    exit /b 1
)
echo [OK] 镜像仓库登录成功

REM 构建镜像
echo.
echo [3/6] 构建Docker镜像...

echo 构建 backend-core 镜像...
docker build -t cr.volcengine.com/ai-agriculture/backend-core:latest -f backend/Dockerfile backend/
if %errorlevel% neq 0 (
    echo [ERROR] backend-core 镜像构建失败
    pause
    exit /b 1
)
echo [OK] backend-core 镜像构建完成

if exist "microservices\api-gateway\Dockerfile" (
    echo 构建 api-gateway 镜像...
    docker build -t cr.volcengine.com/ai-agriculture/api-gateway:latest microservices/api-gateway/
    if %errorlevel% neq 0 (
        echo [WARN] api-gateway 镜像构建失败，继续...
    ) else (
        echo [OK] api-gateway 镜像构建完成
    )
)

if exist "microservices\frontend-web\Dockerfile" (
    echo 构建 frontend-web 镜像...
    docker build -t cr.volcengine.com/ai-agriculture/frontend-web:latest microservices/frontend-web/
    if %errorlevel% neq 0 (
        echo [WARN] frontend-web 镜像构建失败，继续...
    ) else (
        echo [OK] frontend-web 镜像构建完成
    )
)

REM 推送镜像
echo.
echo [4/6] 推送镜像到火山引擎镜像仓库...

echo 推送 backend-core...
docker push cr.volcengine.com/ai-agriculture/backend-core:latest
if %errorlevel% neq 0 (
    echo [ERROR] backend-core 镜像推送失败
    pause
    exit /b 1
)
echo [OK] backend-core 镜像推送完成

docker images | findstr "cr.volcengine.com/ai-agriculture/api-gateway" >nul
if %errorlevel% equ 0 (
    echo 推送 api-gateway...
    docker push cr.volcengine.com/ai-agriculture/api-gateway:latest
    echo [OK] api-gateway 镜像推送完成
)

docker images | findstr "cr.volcengine.com/ai-agriculture/frontend-web" >nul
if %errorlevel% equ 0 (
    echo 推送 frontend-web...
    docker push cr.volcengine.com/ai-agriculture/frontend-web:latest
    echo [OK] frontend-web 镜像推送完成
)

REM 部署到Kubernetes
echo.
echo [5/6] 部署到Kubernetes集群...
kubectl apply -f volcengine-deployment.yaml
if %errorlevel% neq 0 (
    echo [ERROR] Kubernetes部署失败
    pause
    exit /b 1
)
echo [OK] Kubernetes部署完成

REM 等待部署完成
echo.
echo [6/6] 等待部署完成...
timeout /t 10 /nobreak >nul

REM 检查部署状态
echo.
echo 部署状态检查:
echo.
echo Pods:
kubectl get pods -n ai-agriculture
echo.
echo Services:
kubectl get services -n ai-agriculture
echo.
echo Ingress:
kubectl get ingress -n ai-agriculture

REM 获取访问地址
echo.
echo 访问地址:
for /f "tokens=*" %%a in ('kubectl get ingress -n ai-agriculture -o jsonpath="{.items[0].status.loadBalancer.ingress[0].ip}" 2^>nul') do (
    if not "%%a"=="" (
        echo   前端地址: http://%%a/
        echo   API地址: http://%%a/api
        echo   文档地址: http://%%a/docs
    ) else (
        echo   Ingress IP尚未分配，请稍后检查: kubectl get ingress -n ai-agriculture
    )
)

echo.
echo ========================================
echo   部署完成!
echo ========================================
echo.
echo 常用命令:
echo   查看Pod日志: kubectl logs -n ai-agriculture ^<pod-name^>
echo   查看所有资源: kubectl get all -n ai-agriculture
echo   删除部署: kubectl delete -f volcengine-deployment.yaml
echo.
pause
