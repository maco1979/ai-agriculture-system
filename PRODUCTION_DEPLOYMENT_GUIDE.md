# AI农业决策系统 - 生产部署指南

## 部署状态
- 数据库: Supabase (已配置)
- 后端: Railway (待部署)
- 前端: Vercel (待部署)
- 预计上线时间: 今天

## 1. Supabase数据库初始化

### 已配置信息
- 项目URL: https://hephjdmwdaqgiwyppfbd.supabase.co
- 数据库连接: postgresql://postgres:[密码]@db.hephjdmwdaqgiwyppfbd.supabase.co:5432/postgres
- anon key: [匿名密钥]
- service_role key: [服务角色密钥]

### 初始化步骤
1. 登录Supabase: https://supabase.com/dashboard
2. 进入项目: hephjdmwdaqgiwyppfbd
3. 左侧菜单 → SQL Editor → New query
4. 复制 `backend/init.sql` 内容并执行
5. 验证表创建:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```

## 2. Railway后端部署

### Railway配置
- 项目文件: `backend/railway.json`
- 环境变量: `backend/railway.toml`
- 启动命令: `uvicorn main:app --host 0.0.0.0 --port $PORT`

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
- 构建命令: `npm run build`
- 输出目录: `dist/`
- 配置文件: `frontend/vercel.json`

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
   - `VITE_API_BASE_URL`: Railway后端URL
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