# 🌱 AI 农业智能决策系统 — 前端

基于 **Next.js 15 + Supabase** 构建的 AI 农业智能决策系统 Web 前端，提供用户认证、数据可视化与农业决策支持界面。

## 技术栈

| 层级 | 技术 |
|------|------|
| 框架 | Next.js 15 (App Router) |
| 认证 | Supabase Auth（邮箱/密码） |
| 样式 | Tailwind CSS |
| UI 组件 | shadcn/ui |
| 语言 | TypeScript |

## 功能模块

- **用户认证**：登录、注册、忘记密码、密码重置（接入 Supabase Auth 真实 API）
- **路由保护**：Middleware 层自动刷新 Session，未登录用户重定向至登录页
- **个人中心**：展示当前登录账户信息与功能模块入口
- **安全防护**：修复开放重定向漏洞，`auth/confirm` 只允许相对路径跳转

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env.local`，填入 Supabase 项目信息：

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

> 在 [Supabase 控制台 → Project Settings → API](https://supabase.com/dashboard/project/_/settings/api) 获取上述值。

### 3. 启动开发服务器

```bash
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000)

## 项目结构

```
ai-agriculture-system/
├── app/
│   ├── page.tsx                  # 首页（功能介绍 + 登录/注册入口）
│   ├── protected/
│   │   ├── layout.tsx            # 已登录布局（导航 + 退出）
│   │   └── page.tsx              # 个人中心（用户信息 + 功能卡片）
│   └── auth/
│       ├── confirm/route.ts      # 邮箱确认回调（Code Exchange）
│       ├── error/page.tsx        # 认证错误页
│       ├── sign-in/page.tsx      # 登录页
│       ├── sign-up/page.tsx      # 注册页
│       ├── forgot-password/      # 忘记密码
│       └── update-password/      # 密码重置
├── components/
│   ├── login-form.tsx            # 登录表单（Supabase signInWithPassword）
│   ├── sign-up-form.tsx          # 注册表单（Supabase signUp + 邮件验证）
│   ├── forgot-password-form.tsx  # 忘记密码表单（resetPasswordForEmail）
│   ├── update-password-form.tsx  # 密码更新表单（updateUser）
│   ├── logout-button.tsx         # 退出登录（Supabase signOut）
│   └── ui/                       # shadcn/ui 组件库
├── lib/
│   └── supabase/
│       ├── client.ts             # 浏览器端 Supabase 客户端
│       ├── server.ts             # 服务端 Supabase 客户端
│       └── proxy.ts              # Middleware Session 刷新
└── middleware.ts                 # 路由保护 + Session 自动刷新
```

## 认证流程

```
注册 → 发送确认邮件 → /auth/confirm?code=xxx → 交换 Session → /protected
登录 → signInWithPassword → /protected
忘记密码 → 发送重置邮件 → /auth/update-password → updateUser → /protected
```

## 相关服务

本前端配合以下后端服务使用：

- **AI 决策后端**（Python/FastAPI）：`../backend/`
- **API 网关**：`../api-gateway/`
- **区块链溯源**：`../blockchain-integration/`

## 构建部署

```bash
# 构建生产版本
npm run build

# 启动生产服务器
npm run start
```
