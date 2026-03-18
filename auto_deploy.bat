@echo off
echo ===========================================
echo AI农业决策系统 - 自动化部署脚本
echo ===========================================
echo.

echo 步骤1: 检查必要工具
echo.

REM 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装
    echo 请先安装Node.js: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js已安装

REM 检查npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ npm未安装
    pause
    exit /b 1
)
echo ✅ npm已安装

echo.
echo 步骤2: 安装CLI工具
echo.

echo 安装Railway CLI...
call npm install -g @railway/cli
if %errorlevel% neq 0 (
    echo ❌ Railway CLI安装失败
    pause
    exit /b 1
)
echo ✅ Railway CLI安装成功

echo.
echo 安装Vercel CLI...
call npm install -g vercel
if %errorlevel% neq 0 (
    echo ❌ Vercel CLI安装失败
    pause
    exit /b 1
)
echo ✅ Vercel CLI安装成功

echo.
echo 安装Supabase CLI...
call npm install -g supabase
if %errorlevel% neq 0 (
    echo ❌ Supabase CLI安装失败
    echo 注意: Supabase CLI需要Docker
    pause
    exit /b 1
)
echo ✅ Supabase CLI安装成功

echo.
echo ===========================================
echo 部署指南:
echo ===========================================
echo.
echo 1. 数据库部署 (Supabase):
echo   打开新终端，执行:
echo   supabase login
echo   supabase link --project-ref hephjdmwdaqgiwyppfbd
echo   supabase db push
echo.
echo 2. 后端部署 (Railway):
echo   打开新终端，执行:
echo   cd backend
echo   railway login
echo   railway init
echo   railway up
echo.
echo 3. 前端部署 (Vercel):
echo   打开新终端，执行:
echo   cd frontend
echo   vercel login
echo   vercel --prod
echo.
echo 注意: 每个步骤需要登录你的账户
echo.
pause