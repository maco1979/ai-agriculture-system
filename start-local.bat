@echo off
chcp 65001 >nul
title AI 农业决策系统 - 本地启动

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║       AI 农业决策系统  本地开发环境启动              ║
echo ║       后端 :8001   前端 :3000                       ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: ── 检查 Python ──────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 python，请先安装 Python 3.9+
    pause & exit /b 1
)

:: ── 检查 Node.js ─────────────────────────────────────────
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 node，请先安装 Node.js 18+
    pause & exit /b 1
)

:: ── 安装前端依赖（如果 node_modules 不存在）─────────────
if not exist "frontend\node_modules" (
    echo [1/2] 安装前端依赖 npm install ...
    cd frontend
    call npm install
    cd ..
    echo [OK] 前端依赖安装完成
) else (
    echo [1/2] 前端依赖已存在，跳过安装
)

:: ── 安装后端精简依赖 ────────────────────────────────────
echo [2/2] 检查后端依赖 ...
cd backend
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo     安装后端核心依赖（精简，跳过 JAX/硬件依赖）...
    pip install fastapi uvicorn[standard] pydantic python-dotenv loguru ^
                httpx requests typing_extensions pyjwt bcrypt cryptography ^
                --quiet
)
cd ..

echo.
echo ── 启动后端（端口 8001）─────────────────────────────────
start "Backend :8001" cmd /k "cd /d %~dp0backend && set PYTHONPATH=%~dp0backend && python start_simple.py"

:: 等后端启动
timeout /t 3 /nobreak >nul

echo ── 启动前端（端口 3000）─────────────────────────────────
start "Frontend :3000" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [OK] 两个窗口正在启动，请稍候...
echo.
echo   前端地址:  http://localhost:3000
echo   后端 API:  http://localhost:8001/docs
echo   API文档:   http://localhost:8001/redoc
echo.
echo 关闭对应窗口即可停止服务。
echo.

:: 3 秒后自动打开浏览器
timeout /t 5 /nobreak >nul
start http://localhost:3000

pause
