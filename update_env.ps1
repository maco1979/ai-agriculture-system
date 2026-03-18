# AI农业决策系统 - 环境变量更新脚本

param(
    [string]$DatabaseUrl,
    [string]$JwtSecretKey,
    [string]$SupabaseUrl,
    [string]$SupabaseAnonKey,
    [string]$SupabaseServiceKey
)

Write-Host "🔧 更新环境变量配置..." -ForegroundColor Green

# 检查参数
if (-not $DatabaseUrl) {
    $DatabaseUrl = Read-Host "请输入Supabase数据库连接字符串"
}

if (-not $JwtSecretKey) {
    $JwtSecretKey = Read-Host "请输入JWT密钥 (生成命令: openssl rand -base64 32)"
}

if (-not $SupabaseUrl) {
    $SupabaseUrl = Read-Host "请输入Supabase项目URL (格式: https://hephjdmwdaqgiwyppfbd.supabase.co)"
}

if (-not $SupabaseAnonKey) {
    $SupabaseAnonKey = Read-Host "请输入Supabase anon/public key"
}

if (-not $SupabaseServiceKey) {
    $SupabaseServiceKey = Read-Host "请输入Supabase service_role key (保密)"
}

# 更新生产环境配置
$envProduction = ".env.production"
$content = Get-Content $envProduction -Raw

# 替换占位符
$content = $content -replace 'DATABASE_URL=.*', "DATABASE_URL=$DatabaseUrl"
$content = $content -replace 'JWT_SECRET_KEY=.*', "JWT_SECRET_KEY=$JwtSecretKey"
$content = $content -replace 'SUPABASE_URL=.*', "SUPABASE_URL=$SupabaseUrl"
$content = $content -replace 'SUPABASE_ANON_KEY=.*', "SUPABASE_ANON_KEY=$SupabaseAnonKey"
$content = $content -replace 'SUPABASE_SERVICE_KEY=.*', "SUPABASE_SERVICE_KEY=$SupabaseServiceKey"

# 添加Supabase配置（如果不存在）
if (-not ($content -match 'SUPABASE_URL=')) {
    $content += "`n# Supabase配置`n"
    $content += "SUPABASE_URL=$SupabaseUrl`n"
    $content += "SUPABASE_ANON_KEY=$SupabaseAnonKey`n"
    $content += "SUPABASE_SERVICE_KEY=$SupabaseServiceKey`n"
}

Set-Content -Path $envProduction -Value $content
Write-Host "✅ 生产环境配置已更新: $envProduction" -ForegroundColor Green

# 更新本地测试配置（可选）
$updateLocal = Read-Host "是否也更新本地测试配置? (y/n)"
if ($updateLocal -eq 'y') {
    $envLocal = ".env.local"
    if (Test-Path $envLocal) {
        $localContent = Get-Content $envLocal -Raw
        $localContent = $localContent -replace 'DATABASE_URL=.*', "DATABASE_URL=$DatabaseUrl"
        $localContent = $localContent -replace 'JWT_SECRET_KEY=.*', "JWT_SECRET_KEY=$JwtSecretKey"
        Set-Content -Path $envLocal -Value $localContent
        Write-Host "✅ 本地测试配置已更新: $envLocal" -ForegroundColor Green
    }
}

# 复制到backend目录
Copy-Item $envProduction "backend\.env.production" -Force
Write-Host "✅ 配置已复制到backend目录" -ForegroundColor Green

# 显示配置摘要
Write-Host ""
Write-Host "📋 配置摘要:" -ForegroundColor Cyan
Write-Host "数据库URL: $($DatabaseUrl.Substring(0, [Math]::Min(50, $DatabaseUrl.Length)))..." -ForegroundColor White
Write-Host "JWT密钥: $($JwtSecretKey.Substring(0, [Math]::Min(20, $JwtSecretKey.Length)))..." -ForegroundColor White
Write-Host "Supabase URL: $SupabaseUrl" -ForegroundColor White
Write-Host "配置完成！" -ForegroundColor Green