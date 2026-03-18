# 简单部署脚本 - 分步执行

Write-Host "🚀 AI农业决策系统 - 简单部署脚本" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# 步骤1: 检查环境
Write-Host "`n步骤1: 检查环境..." -ForegroundColor Yellow

$nodeVersion = node --version 2>$null
if ($nodeVersion) {
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Node.js未安装" -ForegroundColor Red
    Write-Host "请先安装Node.js: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$npmVersion = npm --version 2>$null
if ($npmVersion) {
    Write-Host "✅ npm: $npmVersion" -ForegroundColor Green
} else {
    Write-Host "❌ npm未安装" -ForegroundColor Red
    exit 1
}

# 步骤2: 安装CLI工具
Write-Host "`n步骤2: 安装CLI工具..." -ForegroundColor Yellow

$tools = @(
    @{Name="Vercel CLI"; Command="npm install -g vercel"},
    @{Name="Railway CLI"; Command="npm install -g @railway/cli"},
    @{Name="Supabase CLI"; Command="npm install -g supabase"}
)

foreach ($tool in $tools) {
    Write-Host "安装 $($tool.Name)..." -ForegroundColor White
    try {
        Invoke-Expression $tool.Command 2>$null
        Write-Host "✅ $($tool.Name) 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "⚠ $($tool.Name) 安装可能有问题" -ForegroundColor Yellow
    }
}

# 步骤3: 显示部署命令
Write-Host "`n步骤3: 部署命令 (按顺序执行)" -ForegroundColor Yellow
Write-Host "=" * 50 -ForegroundColor Cyan

Write-Host "`nA. Supabase数据库部署:" -ForegroundColor Magenta
Write-Host @"
1. 打开新PowerShell窗口
2. 执行:
   supabase login
   supabase link --project-ref hephjdmwdaqgiwyppfbd
   supabase db push
"@ -ForegroundColor White

Write-Host "`nB. Railway后端部署:" -ForegroundColor Magenta
Write-Host @"
1. 打开新PowerShell窗口
2. 执行:
   cd ""$PWD\backend""
   railway login
   railway init
   railway up
"@ -ForegroundColor White

Write-Host "`nC. Vercel前端部署:" -ForegroundColor Magenta
Write-Host @"
1. 打开新PowerShell窗口
2. 执行:
   cd ""$PWD\frontend""
   vercel login
   vercel --prod
"@ -ForegroundColor White

# 步骤4: 测试命令
Write-Host "`n步骤4: 测试命令 (部署后执行)" -ForegroundColor Yellow
Write-Host @"
# 测试后端健康
curl https://ai-agriculture-backend.up.railway.app/health

# 测试前端
# 打开浏览器访问Vercel提供的URL
"@ -ForegroundColor White

# 步骤5: 故障排除
Write-Host "`n步骤5: 常见问题解决" -ForegroundColor Yellow
Write-Host @"
1. 登录问题:
   - 重新登录: vercel logout && vercel login
   - 检查网络连接

2. 部署失败:
   - 查看日志: railway logs
   - 检查环境变量

3. 数据库连接:
   - 验证Supabase项目状态
   - 检查防火墙设置
"@ -ForegroundColor White

Write-Host "`n" + "=" * 50 -ForegroundColor Green
Write-Host "🎯 开始部署吧！打开3个终端同时执行" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

Write-Host "`n💡 提示: 每个步骤需要你在浏览器中登录账户" -ForegroundColor Cyan
Write-Host "我会在这里等待并提供实时支持！" -ForegroundColor Cyan