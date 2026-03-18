@echo off
echo ========================================
echo AI农业决策系统 - 零成本一键部署脚本
echo ========================================
echo.

echo 步骤1: 检查必要工具
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Git，请先安装 Git
    echo 下载地址: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo [成功] Git 已安装
echo.

echo 步骤2: 创建GitHub仓库
set /p github_username="请输入GitHub用户名: "
set /p repo_name="请输入仓库名(默认: ai-agri-system): "
if "%repo_name%"=="" set repo_name=ai-agri-system

echo.
echo 即将创建仓库: https://github.com/%github_username%/%repo_name%
set /p confirm="确认创建? (y/n): "
if /i "%confirm%" neq "y" (
    echo 取消部署
    pause
    exit /b 0
)

echo.
echo 步骤3: 初始化Git仓库
if exist ".git" (
    echo [信息] Git仓库已存在
) else (
    git init
    git add .
    git commit -m "初始提交: AI农业决策系统"
)

echo.
echo 步骤4: 推送到GitHub
echo 请确保已登录GitHub并创建仓库: %repo_name%
echo 或者按Ctrl+C取消，手动创建后继续
pause

git remote add origin https://github.com/%github_username%/%repo_name%.git
git branch -M main
git push -u origin main

if %errorlevel% neq 0 (
    echo [警告] 推送失败，请手动推送
    echo 命令: git push -u origin main
    pause
)

echo.
echo 步骤5: 部署指南
echo ========================================
echo 请按以下步骤完成部署:
echo.
echo 1. 前端部署 (Vercel)
echo    访问: https://vercel.com
echo    使用GitHub登录
echo    导入仓库: %repo_name%
echo    选择目录: frontend/
echo    自动部署完成
echo.
echo 2. 数据库设置 (Supabase)
echo    访问: https://supabase.com
echo    创建新项目: ai-agri-db
echo    地区选择: East Asia
echo    按照 supabase-setup.md 设置数据库
echo.
echo 3. 后端部署 (Railway)
echo    访问: https://railway.app
echo    新建项目，从GitHub部署
echo    选择目录: backend/
echo    配置环境变量 (参考 railway.json)
echo.
echo 4. 配置连接
echo    修改 frontend/.env 中的 API_URL
echo    测试前后端连接
echo.
echo 详细步骤请查看: 部署指南.md
echo ========================================
echo.
echo 部署完成！现在可以开始获取用户和赚钱了！
echo.
pause