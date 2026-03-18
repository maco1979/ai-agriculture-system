# AI农业决策系统 - 最终配置更新脚本

param(
    [Parameter(Mandatory=$true)]
    [string]$DatabasePassword,
    
    [Parameter(Mandatory=$true)]
    [string]$JwtSecret
)

Write-Host "🎯 开始最终配置更新..." -ForegroundColor Green

# 1. 更新生产环境配置
$envFile = ".env.production"
$content = Get-Content $envFile -Raw

# 替换占位符
$content = $content -replace 'YOUR_DATABASE_PASSWORD_HERE', $DatabasePassword
$content = $content -replace 'YOUR_GENERATED_JWT_SECRET_HERE', $JwtSecret

# 添加SECRET_KEY（如果没有）
if (-not ($content -match 'SECRET_KEY=')) {
    $secretKey = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    $content = $content -replace 'SECRET_KEY=\[GENERATE-ANOTHER-SECURE-RANDOM-KEY\]', "SECRET_KEY=$secretKey"
}

Set-Content -Path $envFile -Value $content
Write-Host "✅ 生产环境配置已更新" -ForegroundColor Green

# 2. 复制到backend目录
Copy-Item $envFile "backend\.env" -Force
Copy-Item $envFile "backend\.env.production" -Force
Write-Host "✅ 配置已复制到backend目录" -ForegroundColor Green

# 3. 创建Supabase连接测试脚本
$supabaseTest = @"
# Supabase数据库连接测试脚本
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.production')

def test_supabase_connection():
    try:
        # 获取连接字符串
        database_url = os.getenv('DATABASE_URL')
        print(f"连接字符串: {database_url[:50]}...")
        
        # 连接数据库
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # 测试查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL版本: {version[0]}")
        
        # 检查表
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"✅ 找到 {len(tables)} 张表")
        
        for table in tables[:5]:  # 显示前5张表
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)
"@

Set-Content -Path "test_supabase.py" -Value $supabaseTest
Write-Host "✅ 创建Supabase测试脚本: test_supabase.py" -ForegroundColor Green

# 4. 显示配置摘要
Write-Host "`n📋 配置摘要:" -ForegroundColor Cyan
Write-Host "Supabase项目: hephjdmwdaqgiwyppfbd" -ForegroundColor White
Write-Host "数据库URL: postgresql://postgres:******@db.hephjdmwdaqgiwyppfbd.supabase.co:5432/postgres" -ForegroundColor White
Write-Host "anon key: [SUPABASE_ANON_KEY]" -ForegroundColor White
Write-Host "service_role key: [SUPABASE_SERVICE_ROLE_KEY]" -ForegroundColor White

# 5. 下一步指令
Write-Host "`n🚀 下一步行动:" -ForegroundColor Yellow
Write-Host "1. 测试数据库连接: cd backend && .\venv\Scripts\activate && python ..\test_supabase.py" -ForegroundColor White
Write-Host "2. 初始化数据库: 在Supabase SQL编辑器中执行 backend/init.sql" -ForegroundColor White
Write-Host "3. 测试后端启动: cd backend && .\venv\Scripts\activate && python main.py" -ForegroundColor White
Write-Host "4. 选择部署平台:" -ForegroundColor White
Write-Host "   - Azure: 需要安装Azure CLI和账户" -ForegroundColor White
Write-Host "   - Vercel+Railway: 完全免费，立即部署" -ForegroundColor White

Write-Host "`n🎉 配置更新完成！" -ForegroundColor Green