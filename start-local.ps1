# ============================================================
# AI农业决策系统 - Windows 一键本地启动脚本
# 用法：右键 -> 用 PowerShell 运行，或 .\start-local.ps1
# ============================================================

param(
    [switch]$Stop,        # 停止服务：.\start-local.ps1 -Stop
    [switch]$Rebuild,     # 重新构建：.\start-local.ps1 -Rebuild
    [switch]$Logs,        # 查看日志：.\start-local.ps1 -Logs
    [switch]$Tunnel       # 同时启动 Cloudflare Tunnel
)

$ErrorActionPreference = "Continue"
$ProjectName = "ai-agriculture"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── 颜色输出 ──────────────────────────────────────────
function Write-Step  { param($msg) Write-Host "  → $msg" -ForegroundColor Cyan }
function Write-Ok    { param($msg) Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Fail  { param($msg) Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-Title { param($msg) Write-Host "`n$msg" -ForegroundColor Magenta }

Write-Title "🌾 AI农业决策系统 - 本地启动器"
Write-Host "  时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

Set-Location $ScriptDir

# ── 处理停止命令 ──────────────────────────────────────
if ($Stop) {
    Write-Step "停止所有服务..."
    docker compose -p $ProjectName down
    Write-Ok "服务已停止"
    exit 0
}

# ── 处理日志命令 ──────────────────────────────────────
if ($Logs) {
    docker compose -p $ProjectName logs -f --tail=100
    exit 0
}

# ── 检查依赖 ─────────────────────────────────────────
Write-Title "📋 检查环境依赖"

# 检查 Docker
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "未找到 Docker！"
    Write-Host "  请先安装 Docker Desktop：https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}
Write-Ok "Docker: $dockerVersion"

# 检查 Docker 是否在运行
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Docker Desktop 未启动！请先启动 Docker Desktop，再运行此脚本。"
    Read-Host "按回车退出"
    exit 1
}
Write-Ok "Docker Desktop 运行正常"

# ── 检查/创建 .env 文件 ──────────────────────────────
Write-Title "🔧 环境变量配置"

if (-not (Test-Path ".env")) {
    Write-Warn ".env 文件不存在，从模板创建..."
    Copy-Item ".env.example" ".env"
    Write-Ok ".env 已从模板创建"
    Write-Warn "如需自定义配置，请编辑 .env 文件"
} else {
    Write-Ok ".env 文件已存在"
}

# ── 构建和启动 ───────────────────────────────────────
Write-Title "🐳 启动 Docker 服务"

if ($Rebuild) {
    Write-Step "重新构建镜像（这需要几分钟）..."
    docker compose -p $ProjectName build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "构建失败！查看上方错误信息。"
        Read-Host "按回车退出"
        exit 1
    }
    Write-Ok "镜像构建完成"
}

Write-Step "启动服务（首次启动会构建镜像，需要 3-10 分钟）..."
docker compose -p $ProjectName up -d --build 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Fail "启动失败！尝试运行 '.\start-local.ps1 -Rebuild' 重新构建"
    exit 1
}

# ── 等待服务就绪 ─────────────────────────────────────
Write-Title "⏳ 等待服务启动"

$maxWait = 60
$interval = 3
$elapsed = 0
$backendOk = $false

while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendOk = $true
            break
        }
    } catch {
        Write-Host "  等待后端启动... ($elapsed/$maxWait 秒)" -ForegroundColor Gray
    }
}

# ── 显示结果 ─────────────────────────────────────────
Write-Title "📊 服务状态"
docker compose -p $ProjectName ps

Write-Title "🌐 访问地址"
if ($backendOk) {
    Write-Ok "后端 API:    http://localhost:8000"
    Write-Ok "API 文档:    http://localhost:8000/docs"
    Write-Ok "前端界面:    http://localhost:3000"
    Write-Ok "Redis:       localhost:6379"
} else {
    Write-Warn "后端启动超时，可能仍在初始化中（AI 模型加载需要时间）"
    Write-Host "  稍后手动访问：http://localhost:8000/health" -ForegroundColor Gray
}

# ── Cloudflare Tunnel ────────────────────────────────
if ($Tunnel) {
    Write-Title "🌏 启动 Cloudflare Tunnel（公网访问）"
    
    $cloudflaredPath = Get-Command cloudflared -ErrorAction SilentlyContinue
    if (-not $cloudflaredPath) {
        Write-Warn "未找到 cloudflared，正在安装..."
        winget install Cloudflare.cloudflared 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "winget 安装失败，请手动安装："
            Write-Host "  下载地址：https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Yellow
        }
    }
    
    if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
        Write-Step "启动 Tunnel（生成临时公网 URL）..."
        Write-Host "  注意：临时 URL 每次重启会变，如需固定 URL 请注册 Cloudflare 账号" -ForegroundColor Yellow
        Write-Host ""
        
        # 在新窗口中启动前端 tunnel
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared tunnel --url http://localhost:3000; Read-Host '前端 Tunnel 已关闭，按回车退出'" -WindowStyle Normal
        
        # 当前窗口启动后端 tunnel
        Write-Ok "前端 Tunnel 已在新窗口启动"
        Write-Step "启动后端 Tunnel..."
        cloudflared tunnel --url http://localhost:8000
    }
} else {
    Write-Title "💡 公网访问提示"
    Write-Host "  如需公网访问，运行：" -ForegroundColor Cyan
    Write-Host "  .\start-local.ps1 -Tunnel" -ForegroundColor White
    Write-Host ""
    Write-Host "  或手动运行：" -ForegroundColor Cyan
    Write-Host "  cloudflared tunnel --url http://localhost:3000" -ForegroundColor White
}

Write-Title "📌 常用命令"
Write-Host "  停止服务:   .\start-local.ps1 -Stop" -ForegroundColor Gray
Write-Host "  查看日志:   .\start-local.ps1 -Logs" -ForegroundColor Gray
Write-Host "  重新构建:   .\start-local.ps1 -Rebuild" -ForegroundColor Gray
Write-Host "  开启公网:   .\start-local.ps1 -Tunnel" -ForegroundColor Gray
Write-Host ""
