# AI农业决策系统 - 部署检查清单

## ✅ 已完成

### 基础设施配置
- [x] Azure Bicep基础设施代码 (`infra/`)
- [x] azure.yaml部署配置
- [x] 环境变量模板 (`.env.production`, `.env.local`)
- [x] 数据库初始化脚本 (`backend/init.sql`)
- [x] 部署脚本 (`deploy.ps1`, `deploy.sh`)

### Supabase配置
- [x] Supabase项目创建: `hephjdmwdaqgiwyppfbd`
- [x] 项目URL: `https://hephjdmwdaqgiwyppfbd.supabase.co`
- [x] anon/public key: `sb_publishable_6RC2Qu0yjbsTNwZw9J3KHg_BRGE6c5c`
- [x] 数据库连接字符串模板

### 开发环境
- [x] Python虚拟环境设置
- [x] 后端依赖安装 (FastAPI, SQLAlchemy等)
- [x] 前端依赖安装 (React, Vite, TailwindCSS)
- [x] 前端构建测试

## ⏳ 等待信息（需要老板提供）

### Supabase剩余信息
- [ ] **数据库密码**: 创建项目时设置的密码
- [ ] **service_role key**: Settings → API → service_role key
- [ ] **JWT Secret**: Settings → API → JWT Secret
- [ ] **生成JWT密钥**: 运行命令生成强随机密钥
- [ ] **生成SECRET_KEY**: 另一个随机密钥

### Azure配置
- [ ] **Azure账户**: 注册Azure账号（免费¥2000额度）
- [ ] **Azure CLI安装**: 安装Azure命令行工具
- [ ] **Azure订阅**: 设置默认订阅

## 🔧 待执行任务

### 立即执行（信息齐全后）
1. **更新环境变量** - 使用完整Supabase信息
2. **初始化数据库** - 在Supabase执行SQL脚本
3. **测试数据库连接** - 验证后端能连接Supabase
4. **构建Docker镜像** - 如果Docker服务正常
5. **本地完整测试** - 前后端联调

### Azure部署步骤
1. **安装Azure CLI**
2. **登录Azure账户** `az login`
3. **初始化AZD** `azd init`
4. **配置环境变量** `azd env set`
5. **执行部署** `azd up`

## 📋 信息收集模板

### 请老板提供以下信息：

```
### Supabase信息
1. 数据库密码: [你设置的密码]
2. service_role key: [从Supabase控制台获取]
3. JWT Secret: [从Supabase控制台获取或生成]

### 生成的密钥（运行以下命令）
# PowerShell生成JWT密钥
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

# 生成SECRET_KEY（另一个密钥）
[System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

### Azure账户
1. 是否有Azure账户？ [是/否]
2. 是否需要帮助注册？ [是/否]
```

## 🚨 紧急备用方案

如果Docker持续有问题：

### 方案A：Python直接运行
```bash
# 后端
cd backend
.\venv\Scripts\activate
python main.py

# 前端
cd frontend
npm run dev
```

### 方案B：Azure自动构建
- 使用GitHub Actions自动构建Docker镜像
- Azure Container Apps从GitHub直接部署

### 方案C：简化部署
- 前端部署到Vercel/Netlify（免费）
- 后端部署到Railway/Render（免费额度）
- 数据库使用Supabase（已配置）

## 📞 技术支持

### 问题排查
1. **数据库连接失败**: 检查密码和防火墙
2. **构建失败**: 检查依赖版本和网络
3. **部署失败**: 检查Azure配额和权限

### 资源链接
- Supabase文档: https://supabase.com/docs
- Azure文档: https://learn.microsoft.com/azure
- 项目文档: 查看项目内各指南文件

---

**最后更新: 2026-03-16**
**状态: 等待关键信息**