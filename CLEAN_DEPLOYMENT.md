# 干净部署指南

## 问题分析

部署失败的主要原因是GitHub仓库中包含敏感密钥信息，导致推送被GitHub的安全保护机制阻止。

## 解决方案：创建干净的部署版本

### 1. 创建干净的后端目录

**步骤1：创建新的后端目录**
```bash
mkdir -p clean_deployment/backend
```

**步骤2：复制必要的文件**
```bash
# 复制核心文件
cp -r backend/src clean_deployment/backend/
cp backend/main.py clean_deployment/backend/
cp backend/requirements.txt clean_deployment/backend/
cp backend/railway.toml clean_deployment/backend/
cp backend/railway.json clean_deployment/backend/
cp backend/init.sql clean_deployment/backend/

# 复制Dockerfile
cp backend/Dockerfile clean_deployment/backend/
cp backend/Dockerfile.railway clean_deployment/backend/
```

**步骤3：清理敏感信息**
- 确保所有配置文件中不包含硬编码的密钥
- 使用环境变量替代硬编码值

### 2. 创建干净的前端目录

**步骤1：创建新的前端目录**
```bash
mkdir -p clean_deployment/frontend
```

**步骤2：复制必要的文件**
```bash
# 复制核心文件
cp -r frontend/src clean_deployment/frontend/
cp frontend/package.json clean_deployment/frontend/
cp frontend/package-lock.json clean_deployment/frontend/
cp frontend/vercel.json clean_deployment/frontend/
cp frontend/vite.config.ts clean_deployment/frontend/
cp frontend/tsconfig.json clean_deployment/frontend/
cp frontend/tsconfig.node.json clean_deployment/frontend/
cp frontend/index.html clean_deployment/frontend/
cp frontend/tailwind.config.js clean_deployment/frontend/
cp frontend/postcss.config.js clean_deployment/frontend/
cp frontend/components.json clean_deployment/frontend/
```

**步骤3：更新API配置**
- 修改`frontend/src/config.ts`中的API基础URL为Railway后端URL

### 3. 部署步骤

**后端部署（Railway）**
1. 访问：https://railway.app
2. 点击"New Project" → "Deploy from GitHub repo"
3. 选择`clean_deployment/backend`目录
4. 在Railway控制台设置环境变量
5. 部署完成后获取后端URL

**前端部署（Vercel）**
1. 访问：https://vercel.com
2. 点击"Add New..." → "Project"
3. 选择`clean_deployment/frontend`目录
4. 设置`VITE_API_BASE_URL`环境变量为Railway后端URL
5. 部署完成后获取前端URL

**数据库初始化（Supabase）**
1. 访问：https://supabase.com/dashboard
2. 进入项目：hephjdmwdaqgiwyppfbd
3. 执行`clean_deployment/backend/init.sql`脚本

## 环境变量设置

### Railway后端环境变量
- `DATABASE_URL`: `postgresql://postgres:[SUPABASE_DB_PASSWORD]@db.hephjdmwdaqgiwyppfbd.supabase.co:5432/postgres`
- `SUPABASE_URL`: `https://hephjdmwdaqgiwyppfbd.supabase.co`
- `SUPABASE_ANON_KEY`: `[SUPABASE_ANON_KEY]`
- `SUPABASE_SERVICE_ROLE_KEY`: `[SUPABASE_SERVICE_ROLE_KEY]`
- `JWT_SECRET`: `your-secure-jwt-secret`
- `ENVIRONMENT`: `production`

### Vercel前端环境变量
- `VITE_API_BASE_URL`: `https://your-railway-backend-url.up.railway.app`

## 验证步骤

1. **后端验证**：访问 `https://your-railway-backend-url.up.railway.app/health`
2. **前端验证**：访问 Vercel 提供的前端 URL
3. **功能测试**：测试注册/登录、农业决策等功能
4. **数据库验证**：确认数据正确存储和读取

## 故障排除

**部署失败的常见原因**：
1. **依赖安装失败**：检查`requirements.txt`和`package.json`
2. **环境变量缺失**：确保所有必要的环境变量都已设置
3. **端口配置错误**：确认Railway使用`$PORT`环境变量
4. **健康检查失败**：确保`/health`端点正常响应

**解决方法**：
- 查看部署日志获取详细错误信息
- 检查配置文件和环境变量设置
- 验证代码中的导入路径和依赖关系

## 总结

通过创建干净的部署版本并使用Web界面部署，可以绕过GitHub的密钥检测限制，顺利完成系统部署。部署完成后，系统将正常运行并提供完整的AI农业决策功能。