@echo off
chcp 65001 >nul
echo ========================================
echo   AI农业平台 - 火山引擎部署脚本
echo ========================================
echo.

REM 设置变量
set REGISTRY=cr-cn-beijing.volces.com
set NAMESPACE=ai-agriculture
set USERNAME=volcen
set PASSWORD=ZjI5YzAzNDkzMjhkNGY2Y2ZlMjkwOTZiMGVlOTY4YTA

echo [1/6] 检查Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)
echo [OK] Docker已就绪

echo.
echo [2/6] 登录火山引擎镜像仓库...
echo %PASSWORD% | docker login %REGISTRY% -u %USERNAME% --password-stdin
if %errorlevel% neq 0 (
    echo [WARN] 登录失败，尝试使用本地镜像...
)

echo.
echo [3/6] 构建Docker镜像...

cd /d d:\1.6\1.5

echo 构建 backend-core...
docker build -t %REGISTRY%/ai-agriculture/backend-core:latest -f backend/Dockerfile backend/
if %errorlevel% neq 0 (
    echo [ERROR] backend-core 构建失败
    pause
    exit /b 1
)

if exist "microservices\api-gateway\Dockerfile" (
    echo 构建 api-gateway...
    docker build -t %REGISTRY%/ai-agriculture/api-gateway:latest microservices/api-gateway/
)

if exist "microservices\frontend-web\Dockerfile" (
    echo 构建 frontend-web...
    docker build -t %REGISTRY%/ai-agriculture/frontend-web:latest microservices/frontend-web/
)

echo [OK] 镜像构建完成

echo.
echo [4/6] 推送镜像...
docker push %REGISTRY%/ai-agriculture/backend-core:latest
docker push %REGISTRY%/ai-agriculture/api-gateway:latest 2>nul
docker push %REGISTRY%/ai-agriculture/frontend-web:latest 2>nul

echo.
echo [5/6] 检查Kubernetes连接...
kubectl cluster-info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未连接到Kubernetes集群
    echo 请配置KUBECONFIG环境变量
    pause
    exit /b 1
)

echo.
echo [6/6] 部署到Kubernetes...
kubectl apply -f volcengine-deployment.yaml

echo.
echo 等待部署完成...
timeout /t 5 /nobreak >nul

echo.
echo 部署状态:
kubectl get pods -n %NAMESPACE%
kubectl get svc -n %NAMESPACE%

echo.
echo ========================================
echo   部署完成!
echo ========================================
pause
