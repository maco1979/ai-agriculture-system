# Supabase 数据库设置指南

## 🎯 目标：设置免费的 PostgreSQL 数据库

## 步骤1：创建 Supabase 项目

1. **访问** [supabase.com](https://supabase.com)
2. **注册** 使用 GitHub 账号（免费）
3. **新建项目**
   - 组织名：你的组织名
   - 项目名：`ai-agri-db`
   - 数据库密码：设置强密码
   - 地区：选择 `East Asia (Singapore)` 或最近地区
   - 定价计划：选择 **Free Plan**

4. **等待项目创建**（约1-2分钟）

## 步骤2：获取连接信息

项目创建后，在 Dashboard 找到：

### 连接信息
```
项目URL: https://xxxxxxxxxxxx.supabase.co
API密钥: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
数据库密码: 你设置的密码
```

### 连接字符串
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
```

## 步骤3：设置数据库表

### 方法A：使用 SQL 编辑器
1. 进入 **SQL Editor**
2. 创建新查询
3. 运行以下 SQL：

```sql
-- 创建用户表
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  full_name VARCHAR(255),
  subscription_tier VARCHAR(50) DEFAULT 'free',
  subscription_ends_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建农场表
CREATE TABLE farms (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  location VARCHAR(255),
  area_hectares DECIMAL(10,2),
  crop_type VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建决策记录表
CREATE TABLE decisions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
  decision_type VARCHAR(100) NOT NULL,
  parameters JSONB,
  result JSONB,
  confidence_score DECIMAL(5,2),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 创建传感器数据表
CREATE TABLE sensor_data (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
  sensor_type VARCHAR(100),
  value DECIMAL(10,2),
  unit VARCHAR(50),
  recorded_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_farms_user_id ON farms(user_id);
CREATE INDEX idx_decisions_farm_id ON decisions(farm_id);
CREATE INDEX idx_sensor_data_farm_id ON sensor_data(farm_id);
```

### 方法B：使用 Table Editor（可视化）
1. 进入 **Table Editor**
2. 逐个创建表
3. 设置字段和关系

## 步骤4：设置身份验证

### 启用邮箱认证
1. 进入 **Authentication** → **Providers**
2. 启用 **Email**
3. 配置 SMTP（可选，用于发送验证邮件）

### 设置用户策略
进入 **Authentication** → **Policies**，创建策略：

```sql
-- 允许用户管理自己的数据
CREATE POLICY "用户只能访问自己的数据" ON users
FOR ALL USING (auth.uid() = id);

CREATE POLICY "用户只能管理自己的农场" ON farms
FOR ALL USING (auth.uid() = user_id);
```

## 步骤5：设置存储（可选）

### 创建存储桶
1. 进入 **Storage**
2. 创建新存储桶：`farm-images`
3. 设置权限：公开读取，认证用户可写

### 存储策略
```sql
-- 允许用户上传图片
CREATE POLICY "用户可上传图片" ON storage.objects
FOR INSERT WITH CHECK (auth.uid() = owner);

-- 允许公开读取
CREATE POLICY "公开读取图片" ON storage.objects
FOR SELECT USING (bucket_id = 'farm-images');
```

## 步骤6：测试连接

### 使用 Supabase 客户端测试
```javascript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xxxxxxxxxxxx.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'

const supabase = createClient(supabaseUrl, supabaseKey)

// 测试查询
const { data, error } = await supabase
  .from('users')
  .select('*')
  .limit(1)

if (error) {
  console.error('连接失败:', error)
} else {
  console.log('连接成功:', data)
}
```

### 使用 PostgreSQL 客户端测试
```bash
# 使用 psql 连接
psql -h db.xxxxxxxxxxxx.supabase.co -p 5432 -U postgres -d postgres

# 输入密码后测试
SELECT version();
SELECT current_database();
```

## 步骤7：配置到后端

### 环境变量设置
在 Railway 或本地环境设置：

```
DATABASE_URL=postgresql://postgres:[密码]@db.xxxxxxxxxxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=[在设置->API中找到]
```

### Python 连接示例
```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 测试连接
response = supabase.table("users").select("*").limit(1).execute()
print(response.data)
```

## 步骤8：监控和维护

### 监控使用量
1. 进入 **Dashboard** → **Database**
2. 查看：
   - 数据库大小（免费层500MB限制）
   - 活跃连接数
   - 查询性能

### 备份策略
1. **自动备份**：Supabase 每天自动备份
2. **手动备份**：可导出 SQL 文件
3. **时间点恢复**：专业版功能

### 性能优化
1. 添加合适索引
2. 定期清理旧数据
3. 监控慢查询

## 常见问题

### Q1: 免费层限制是什么？
```
A: 每月500MB数据库，50,000行插入，2个活跃项目
```

### Q2: 如何升级？
```
A: 进入 Billing，选择 Pro 计划（$25/月）
```

### Q3: 数据安全吗？
```
A: Supabase 提供企业级安全，但建议定期备份
```

### Q4: 如何迁移现有数据？
```
A: 使用 pg_dump 导出，psql 导入
```

## 下一步

1. ✅ 完成数据库设置
2. ✅ 测试连接
3. ✅ 配置到后端
4. ✅ 开始开发

---

**免费数据库就绪，可以开始构建应用了！** 🚀