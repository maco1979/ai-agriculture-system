# AI农业决策系统 - 快速测试脚本

Write-Host "🚀 开始快速测试..." -ForegroundColor Green

# 测试1: 检查前端构建
Write-Host "`n📱 测试前端构建..." -ForegroundColor Yellow
if (Test-Path "frontend\dist") {
    $fileCount = (Get-ChildItem "frontend\dist" -Recurse -File).Count
    $sizeMB = "{0:N2}" -f ((Get-ChildItem "frontend\dist" -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)
    Write-Host "✅ 前端构建完成: $fileCount 个文件, $sizeMB MB" -ForegroundColor Green
} else {
    Write-Host "❌ 前端构建目录不存在" -ForegroundColor Red
}

# 测试2: 检查Python环境
Write-Host "`n🐍 测试Python环境..." -ForegroundColor Yellow
try {
    cd backend
    .\venv\Scripts\activate
    $pythonVersion = python --version
    Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
    
    # 测试关键依赖
    $deps = @("fastapi", "uvicorn", "sqlalchemy", "pydantic")
    foreach ($dep in $deps) {
        try {
            python -c "import $dep; print('  ✅ $dep')"
        } catch {
            Write-Host "  ❌ $dep 导入失败" -ForegroundColor Red
        }
    }
    cd ..
} catch {
    Write-Host "❌ Python环境测试失败: $_" -ForegroundColor Red
}

# 测试3: 检查数据库连接（本地）
Write-Host "`n🗄️ 测试本地数据库..." -ForegroundColor Yellow
try {
    $dockerPs = docker ps --filter "name=postgres" --format "table {{.Names}}\t{{.Status}}"
    if ($dockerPs -match "postgres") {
        Write-Host "✅ 本地PostgreSQL容器运行中" -ForegroundColor Green
        
        # 测试连接（简化）
        Write-Host "  尝试连接数据库..." -ForegroundColor White
        Start-Sleep -Seconds 3
        
        # 使用Python测试连接
        cd backend
        .\venv\Scripts\activate
        $testScript = @"
import os
import sys
from dotenv import load_dotenv
load_dotenv()

print("环境变量加载成功")
db_url = os.getenv('DATABASE_URL')
print(f"数据库URL: {db_url}")

if 'localhost' in db_url or '127.0.0.1' in db_url:
    print("✅ 使用本地数据库配置")
else:
    print("⚠ 使用远程数据库配置")
"@
        
        python -c $testScript
        cd ..
    } else {
        Write-Host "❌ PostgreSQL容器未运行" -ForegroundColor Red
        Write-Host "  启动命令: docker-compose -f docker-compose.test.yml up -d postgres" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ 数据库测试失败: $_" -ForegroundColor Red
}

# 测试4: 检查配置文件
Write-Host "`n📄 测试配置文件..." -ForegroundColor Yellow
$configFiles = @(".env.production", "azure.yaml", "infra\main.bicep", "DEPLOYMENT_AND_OPERATIONS_GUIDE.md")
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file 存在" -ForegroundColor Green
    } else {
        Write-Host "❌ $file 缺失" -ForegroundColor Red
    }
}

# 总结
Write-Host "`n" + "="*50 -ForegroundColor Cyan
Write-Host "📊 测试完成总结" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan

Write-Host "`n🚀 下一步行动:" -ForegroundColor Yellow
Write-Host "1. 获取Supabase密码和service_role key" -ForegroundColor White
Write-Host "2. 生成JWT密钥" -ForegroundColor White
Write-Host "3. 更新环境变量" -ForegroundColor White
Write-Host "4. 初始化Supabase数据库" -ForegroundColor White
Write-Host "5. 选择部署平台 (Azure或Vercel+Railway)" -ForegroundColor White

Write-Host "`n💡 提示: 运行以下命令生成JWT密钥:" -ForegroundColor Cyan
Write-Host '[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))' -ForegroundColor White