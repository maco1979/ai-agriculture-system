# AI农业决策系统 - 零成本部署步骤

## 📋 准备工作
1. **GitHub账号**：确保你有GitHub账号（用于Railway/Vercel登录）
2. **邮箱**：用于注册Supabase

## 🚀 步骤1：创建Supabase项目（5分钟）

### 1.1 访问并注册
- 打开 https://supabase.com → 点击 **Start your project**
- 使用GitHub或邮箱注册

### 1.2 创建项目
- 点击 **New Project**
- 填写信息：
  - **Name**: `ai-agriculture`（任意）
  - **Database Password**: 设置强密码（记住！）
  - **Region**: 选择离你最近的（如 `ap-southeast-1`）
- 点击 **Create new project**（等待2-3分钟）

### 1.3 获取连接信息
项目创建后，在左侧菜单找到：
1. **Settings → API**：记录
   - `Project URL`（如 `https://xxxxx.supabase.co`）
   - `anon` key（`sb_publishable_...`）
2. **Database → Connection String**：
   - 选择 **URI**，复制类似：
   ```
   postgresql://postgres:[YOUR_PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

### 1.4 初始化数据库
1. 左侧菜单 → **SQL Editor** → **New query**
2. 打开文件 `D:\1.6\1.5\backend\init.sql`，复制全部内容
3. 粘贴到查询编辑器，点击 **Run**
4. 验证表创建：
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```
   应该看到 `users`、`farms` 等表

## 🚀 步骤2：部署后端到Railway（10分钟）

### 2.1 准备GitHub仓库（如果未上传）
```bash
cd "D:\1.6\1.5"
git init
git add .
git commit -m "Initial commit: AI Agriculture Decision System"
# 在GitHub.com创建新仓库，然后：
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 2.2 部署到Railway
1. 访问 https://railway.app → **Login with GitHub**
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 授权并选择你的仓库，路径选择 **`/backend`**
4. Railway会自动：
   - 检测Python项目
   - 安装依赖（`requirements.txt`）
   - 启动容器

### 2.3 配置环境变量
在Railway项目页面：
1. 点击 **Variables** 标签
2. 添加以下变量：
   ```
   DATABASE_URL=你的Supabase数据库URI
   SUPABASE_URL=你的Supabase项目URL
   SUPABASE_ANON_KEY=你的anon key
   JWT_SECRET=生成密钥：运行 `openssl rand -base64 32`
   ENVIRONMENT=production
   ```
   （Windows生成JWT密钥：`python -c "import secrets; print(secrets.token_urlsafe(32))"`）

### 2.4 获取后端URL
部署完成后：
- Railway会分配域名：`https://xxxx.up.railway.app`
- 测试健康检查：`https://xxxx.up.railway.app/health`
- 记录此URL，用于前端配置

## 🚀 步骤3：部署前端到Vercel（5分钟）

### 3.1 部署前端
1. 访问 https://vercel.com → **Login with GitHub**
2. 点击 **Add New Project**
3. 导入你的GitHub仓库
4. 配置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - 其他保持默认

### 3.2 配置环境变量
在Vercel项目设置：
1. 点击 **Settings** → **Environment Variables**
2. 添加：
   ```
   VITE_API_BASE_URL=你的Railway后端URL
   ```
3. 点击 **Save**

### 3.3 部署
- 点击 **Deploy**（等待2-3分钟）
- 获得前端URL：`https://ai-agriculture.vercel.app`

## ✅ 步骤4：测试生产环境

### 4.1 功能测试
1. 访问你的Vercel前端URL
2. 点击 **Sign Up** 注册新用户
3. 登录后测试农业决策功能
4. 检查数据是否保存到Supabase

### 4.2 监控
- **Supabase**: Database → Tables → 查看数据
- **Railway**: 项目 → Logs 查看后端日志
- **Vercel**: Analytics 查看前端访问

## 🆘 故障排除

### 数据库连接失败
- 检查 `DATABASE_URL` 格式是否正确
- 确保Supabase IP允许连接（默认允许所有）

### 后端部署失败
- 检查Railway Logs中的错误信息
- 确保 `requirements.txt` 所有依赖可安装

### 前端API调用失败
- 检查 `VITE_API_BASE_URL` 是否正确
- 浏览器开发者工具 → Network 查看请求

## 📞 支持
如果遇到问题：
1. 截图错误信息
2. 检查Railway/Vercel日志
3. 确保所有环境变量正确

---

**预计总时间：20-30分钟**
**成本：完全免费**（Railway每月5美元免费额度，Vercel免费，Supabase免费层）
**上线后**：系统自动运行，无需维护