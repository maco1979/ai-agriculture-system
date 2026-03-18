# AI农业决策系统 - 前端构建脚本

Write-Host "🚀 开始构建前端应用..." -ForegroundColor Green

# 检查Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js未安装，请先安装Node.js" -ForegroundColor Red
    exit 1
}

# 检查npm
try {
    $npmVersion = npm --version
    Write-Host "✅ npm版本: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm未安装" -ForegroundColor Red
    exit 1
}

# 进入前端目录
Set-Location "frontend"

# 安装依赖
Write-Host "📦 安装依赖包..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 依赖安装失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 依赖安装完成" -ForegroundColor Green

# 构建应用
Write-Host "🔨 构建应用..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 构建失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 应用构建完成" -ForegroundColor Green

# 检查构建结果
$distDir = "dist"
if (Test-Path $distDir) {
    $fileCount = (Get-ChildItem $distDir -Recurse -File).Count
    $totalSize = "{0:N2}" -f ((Get-ChildItem $distDir -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)
    
    Write-Host "📊 构建统计:" -ForegroundColor Cyan
    Write-Host "  文件数量: $fileCount" -ForegroundColor White
    Write-Host "  总大小: $totalSize MB" -ForegroundColor White
    
    # 显示主要文件
    Write-Host "📁 主要文件:" -ForegroundColor Cyan
    Get-ChildItem $distDir -File | ForEach-Object {
        Write-Host "  - $($_.Name) ($("{0:N2}" -f ($_.Length / 1KB)) KB)" -ForegroundColor White
    }
} else {
    Write-Host "❌ 构建目录不存在: $distDir" -ForegroundColor Red
    exit 1
}

# 返回上级目录
Set-Location ".."

Write-Host ""
Write-Host "🎉 前端构建完成！" -ForegroundColor Green
Write-Host "下一步:"
Write-Host "1. 运行本地开发服务器: cd frontend && npm run dev" -ForegroundColor Yellow
Write-Host "2. 构建Docker镜像: docker build -t ai-agriculture-frontend:latest ." -ForegroundColor Yellow
Write-Host "3. 部署到Azure Static Web Apps" -ForegroundColor Yellow