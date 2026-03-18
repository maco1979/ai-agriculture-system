# AI农业决策系统 - Vercel + Railway 一键部署脚本

Write-Host "?? 开始部署到 Vercel + Railway + Supabase..." -ForegroundColor Green
Write-Host "预计时间: 15-30分钟" -ForegroundColor Yellow
Write-Host ""

# 检查必要工具
function Check-Tools {
    Write-Host "?? 检查必要工具..." -ForegroundColor Yellow
    
    $tools = @{
        "Node.js" = "node --version";
        "npm" = "npm --version";
        "Git" = "git --version"
    }
    
    foreach ($tool in $tools.GetEnumerator()) {
        try {
            $version = Invoke-Expression $tool.Value 2>$null
            Write-Host "? $($tool.Key): $version" -ForegroundColor Green
        } catch {
            Write-Host "? $($tool.Key): 未安装" -ForegroundColor Red
            return $false
        }
    }
    
    return $true
}

# 显示部署步骤
function Show-DeploymentSteps {
    Write-Host ""
    Write-Host "?? 部署步骤:" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    Write-Host "`n第1步: 初始化Supabase数据库 (需要手动操作)" -ForegroundColor Yellow
    Write-Host "  1. 登录: https://supabase.com/dashboard/project/hephjdmwdaqgiwyppfbd" -ForegroundColor White
    Write-Host "  2. 打开 SQL Editor → New query" -ForegroundColor White
    Write-Host "  3. 复制并执行: backend\init.sql" -ForegroundColor White
    Write-Host "  4. 验证表创建" -ForegroundColor White
    
    Write-Host "`n第2步: 部署后端到Railway" -ForegroundColor Yellow
    Write-Host "  1. 访问: https://railway.app" -ForegroundColor White
    Write-Host "  2. 点击 'New Project'" -ForegroundColor White
    Write-Host "  3. 选择 'Deploy from GitHub repo'" -ForegroundColor White
    Write-Host "  4. 选择本项目backend目录" -ForegroundColor White
    Write-Host "  5. Railway会自动部署" -ForegroundColor White
    
    Write-Host "`n第3步: 部署前端到Vercel" -ForegroundColor Yellow
    Write-Host "  1. 访问: https://vercel.com" -ForegroundColor White
    Write-Host "  2. 点击 'Add New...' → 'Project'" -ForegroundColor White
    Write-Host "  3. 导入GitHub仓库" -ForegroundColor White
    Write-Host "  4. 选择frontend目录" -ForegroundColor White
    Write-Host "  5. 配置环境变量" -ForegroundColor White
    Write-Host "  6. 点击 'Deploy'" -ForegroundColor White
    
    Write-Host "`n第4步: 测试生产环境" -ForegroundColor Yellow
    Write-Host "  1. 访问Vercel提供的URL" -ForegroundColor White
    Write-Host "  2. 测试注册/登录" -ForegroundColor White
    Write-Host "  3. 测试API调用" -ForegroundColor White
    Write-Host "  4. 验证数据库连接" -ForegroundColor White
}

# 创建GitHub仓库准备脚本
function Prepare-GitHub {
    Write-Host "`n?? 准备GitHub仓库..." -ForegroundColor Yellow
    
    # 检查是否在Git仓库中
    if (Test-Path ".git") {
        Write-Host "? 已在Git仓库中" -ForegroundColor Green
    } else {
        Write-Host "? 未初始化Git仓库" -ForegroundColor Yellow
        $initGit = Read-Host "是否初始化Git仓库? (y/n)"
        if ($initGit -eq 'y') {
            git init
            git add .
            git commit -m "Initial commit: AI Agriculture Decision System"
            Write-Host "? Git仓库已初始化" -ForegroundColor Green
        }
    }
    
    # 创建.gitignore
    $gitignore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.egg-info/

# Logs
*.log
logs/
"@
    
    Set-Content -Path ".gitignore" -Value $gitignore
    Write-Host "? .gitignore已创建" -ForegroundColor Green
}

# 生成部署指南
function Generate-DeploymentGuide {
    $guide = @"
# AI农业决策系统 - 生产部署指南

## 部署状态
- 数据库: Supabase (已配置)
- 后端: Railway (待部署)
- 前端: Vercel (待部署)
- 预计上线时间: 今天

## 1. Supabase数据库初始化

### 已配置信息
- 项目URL: https://hephjdmwdaqgiwyppfbd.supabase.co
- 数据库连接: postgresql://postgres:[SUPABASE_DB_PASSWORD]@db.hephjdmwdaqgiwyppfbd.supabase.co:5432/postgres
- anon key: [SUPABASE_ANON_KEY]
- service_role key: [SUPABASE_SERVICE_ROLE_KEY]

### 初始化步骤
1. 登录Supabase: https://supabase.com/dashboard
2. 进入项目: hephjdmwdaqgiwyppfbd
3. 左侧菜单 → SQL Editor → New query
4. 复制 \`backend/init.sql\` 内容并执行
5. 验证表创建:
   \`\`\`sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public'
   ORDER BY table_name;
   \`\`\`

## 2. Railway后端部署

### Railway配置
- 项目文件: \`backend/railway.json\`
- 环境变量: \`backend/railway.toml\`
- 启动命令: \`uvicorn main:app --host 0.0.0.0 --port \$PORT\`

### 部署步骤
1. 访问: https://railway.app
2. 登录GitHub账户
3. 点击 "New Project"
4. 选择 "Deploy from GitHub repo"
5. 选择本项目的backend目录
6. Railway会自动:
   - 检测Python项目
   - 安装依赖
   - 部署容器
   - 分配域名

### 预期结果
- 后端URL: https://ai-agriculture-backend.up.railway.app
- 健康检查: https://ai-agriculture-backend.up.railway.app/health
- API文档: https://ai-agriculture-backend.up.railway.app/docs

## 3. Vercel前端部署

### Vercel配置
- 框架: Vite (React + TypeScript)
- 构建命令: \`npm run build\`
- 输出目录: \`dist/\`
- 配置文件: \`frontend/vercel.json\`

### 部署步骤
1. 访问: https://vercel.com
2. 登录GitHub账户
3. 点击 "Add New..." → "Project"
4. 导入GitHub仓库
5. 配置:
   - Framework Preset: Vite
   - Root Directory: frontend
   - Build Command: npm run build
   - Output Directory: dist
6. 环境变量:
   - \`VITE_API_BASE_URL\`: Railway后端URL
7. 点击 "Deploy"

### 预期结果
- 前端URL: https://ai-agriculture.vercel.app
- 自动SSL证书
- 全球CDN

## 4. 生产环境测试

### 测试清单
- [ ] 访问前端URL
- [ ] 注册新用户
- [ ] 登录系统
- [ ] 测试农业决策功能
- [ ] 验证数据库连接
- [ ] 检查错误日志

### 监控
- Supabase: 数据库性能和用量
- Railway: 后端日志和资源使用
- Vercel: 前端访问统计和性能

## 5. 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查Supabase防火墙设置
   - 验证密码和密钥
   - 检查网络连接

2. **后端部署失败**
   - 检查Railway日志
   - 验证Python依赖
   - 检查环境变量

3. **前端构建失败**
   - 检查Vercel构建日志
   - 验证Node.js版本
   - 检查依赖冲突

### 支持资源
- Supabase文档: https://supabase.com/docs
- Railway文档: https://docs.railway.app
- Vercel文档: https://vercel.com/docs

## 6. 后续优化

### 性能优化
1. 数据库索引优化
2. API响应缓存
3. 前端代码分割

### 功能增强
1. 移动端适配
2. 多语言支持
3. 实时通知

### 监控告警
1. 错误追踪
2. 性能监控
3. 用户行为分析

---
**部署时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm')**
**状态: 准备部署**
"@
    
    Set-Content -Path "PRODUCTION_DEPLOYMENT_GUIDE.md" -Value $guide
    Write-Host "? 生产部署指南已生成: PRODUCTION_DEPLOYMENT_GUIDE.md" -ForegroundColor Green
}

# 主函数
function Main {
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "AI农业决策系统 - 生产部署" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
    
    # 检查工具
    if (-not (Check-Tools)) {
        Write-Host "? 缺少必要工具，请先安装" -ForegroundColor Red
        exit 1
    }
    
    # 显示部署步骤
    Show-DeploymentSteps
    
    # 准备GitHub
    Prepare-GitHub
    
    # 生成部署指南
    Generate-DeploymentGuide
    
    # 总结
    Write-Host "`n" + "=" * 60 -ForegroundColor Green
    Write-Host "?? 部署准备完成！" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    
    Write-Host "`n?? 立即行动:" -ForegroundColor Yellow
    Write-Host "1. 按照 PRODUCTION_DEPLOYMENT_GUIDE.md 执行部署" -ForegroundColor White
    Write-Host "2. 先初始化Supabase数据库" -ForegroundColor White
    Write-Host "3. 然后部署Railway后端" -ForegroundColor White
    Write-Host "4. 最后部署Vercel前端" -ForegroundColor White
    
    Write-Host "`n?? 需要帮助?" -ForegroundColor Cyan
    Write-Host "- Supabase问题: 检查数据库连接" -ForegroundColor White
    Write-Host "- Railway问题: 查看部署日志" -ForegroundColor White
    Write-Host "- Vercel问题: 检查构建日志" -ForegroundColor White
    
    Write-Host "`n? 预计今天内系统上线运行！" -ForegroundColor Green
}

# 执行主函数
Main
