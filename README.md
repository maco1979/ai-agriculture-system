# AI Agriculture System
# AI农业决策系统 🌱

基于强化学习、区块链和边缘计算的智能农业决策平台。

## 🚀 功能特性

### 核心功能
- **智能决策**：基于强化学习的农业决策优化
- **区块链溯源**：农产品全生命周期追溯
- **边缘计算**：实时数据处理和响应
- **多模态AI**：图像识别、自然语言处理、预测分析

### 技术栈
- **前端**：React + Vite + TypeScript
- **后端**：FastAPI + Python 3.12
- **数据库**：PostgreSQL (Supabase)
- **部署**：Vercel (前端) + Railway (后端)
- **AI框架**：PyTorch + TensorFlow

## 📦 快速开始

### 环境要求
- Node.js 18+
- Python 3.12+
- Git

### 本地开发
```bash
# 克隆仓库
git clone https://github.com/maco1979/ai-agriculture-system.git
cd ai-agriculture-system

# 后端设置
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 前端设置
cd ../frontend
npm install
npm run dev
```

### 环境配置
1. 复制 `.env.example` 为 `.env.production`
2. 配置以下环境变量：
   - `DATABASE_URL`: Supabase PostgreSQL连接
   - `SUPABASE_*`: Supabase项目密钥
   - `JWT_SECRET`: JWT签名密钥

## 🌐 部署指南

### 1. Supabase数据库
1. 创建Supabase项目
2. 执行 `backend/init.sql` 初始化数据库
3. 获取连接信息

### 2. Railway后端
1. 访问 https://railway.app
2. 部署 `backend` 目录
3. 配置环境变量

### 3. Vercel前端
1. 访问 https://vercel.com
2. 部署 `frontend` 目录
3. 设置环境变量 `VITE_API_BASE_URL`

## 🔧 环境变量

### 后端环境变量
```bash
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
JWT_SECRET=your_jwt_secret
ENVIRONMENT=production
```

### 前端环境变量
```bash
VITE_API_BASE_URL=https://backend.up.railway.app
```

## 📁 项目结构

```
ai-agriculture-system/
├── frontend/                 # 前端React应用
│   ├── src/
│   ├── public/
│   └── package.json
├── backend/                  # 后端FastAPI应用
│   ├── src/
│   ├── requirements.txt
│   └── main.py
├── infra/                    # 基础设施代码
├── docs/                     # 文档
├── .env.example             # 环境变量模板
├── docker-compose.yml       # Docker编排
└── README.md               # 项目说明
```

## 🧪 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📈 监控

- **健康检查**：`GET /health`
- **性能监控**：Prometheus + Grafana
- **日志**：结构化日志输出

## 🔒 安全

- JWT身份验证
- CORS配置
- 输入验证
- SQL注入防护
- 速率限制

## 🤝 贡献

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📄 许可证

MIT License

## 📞 支持

- 问题跟踪：GitHub Issues
- 文档：项目Wiki
- 讨论：GitHub Discussions

## 🎯 路线图

- [ ] 移动端应用
- [ ] IoT设备集成
- [ ] 多语言支持
- [ ] 高级分析仪表板
- [ ] 机器学习模型市场

---

**开始使用AI农业决策系统，让农业更智能！** 🌾
