# 阿里云部署指南

## 概述

本指南将帮助您将AI农业决策系统部署到阿里云平台。

## 架构方案

### 推荐架构
- **前端**：阿里云OSS + CDN
- **后端**：阿里云ECS（云服务器）
- **数据库**：阿里云RDS PostgreSQL 或 继续使用Supabase
- **可选**：阿里云负载均衡SLB（如需高可用）

## 一、前端部署（OSS + CDN）

### 1.1 准备工作

1. **注册阿里云账号**
   - 访问：https://www.aliyun.com
   - 完成实名认证
   - 新用户可领取免费额度

2. **开通OSS服务**
   - 访问：https://oss.console.aliyun.com
   - 点击"创建Bucket"
   - 填写配置：
     - Bucket名称：`ai-agriculture-frontend`（全局唯一）
     - 地域：选择离您最近的地域
     - 存储类型：标准存储
     - 读写权限：公共读

3. **开通CDN服务**
   - 访问：https://cdn.console.aliyun.com
   - 点击"添加域名"
   - 绑定您的域名（如：`ai.yourdomain.com`）

### 1.2 部署步骤

#### 步骤1：构建前端项目
```bash
cd frontend
npm install
npm run build
```

#### 步骤2：上传到OSS

**方式一：使用阿里云控制台**
1. 进入OSS控制台
2. 选择您的Bucket
3. 点击"文件管理" → "上传文件"
4. 将`frontend/dist`目录下的所有文件上传

**方式二：使用OSS Browser工具**
1. 下载OSS Browser：https://help.aliyun.com/document_detail/209974.html
2. 使用AccessKey登录
3. 拖拽`dist`目录内容到Bucket中

**方式三：使用命令行工具（ossutil）**
```bash
# 下载并安装ossutil
# 配置AccessKey
ossutil config

# 上传文件
ossutil cp -r frontend/dist/ oss://ai-agriculture-frontend/
```

#### 步骤3：配置静态网站托管
1. 进入OSS控制台 → 您的Bucket
2. 点击"数据管理" → "静态页面"
3. 开启"静态网站托管"
4. 设置：
   - 默认首页：`index.html`
   - 404页面：`index.html`（重要！解决前端路由问题）

#### 步骤4：配置CDN
1. 进入CDN控制台
2. 点击"域名管理" → 您的域名
3. 配置：
   - 源站类型：OSS域名
   - 源站地址：选择您的OSS Bucket域名
4. 配置缓存规则
5. 等待CDN生效（约5-10分钟）

### 1.3 验证前端部署

访问您的CDN域名或OSS域名，确认页面正常显示。

## 二、后端部署（ECS）

### 2.1 准备工作

#### 步骤1：购买/领取ECS

**新用户免费方案**：
1. 访问：https://free.aliyun.com
2. 领取"云服务器ECS"免费试用
3. 选择配置：
   - 操作系统：Ubuntu 22.04 LTS
   - 实例规格：2核4GB（最低配置）
   - 带宽：1Mbps
   - 系统盘：40GB

**付费方案**：
1. 访问：https://ecs.console.aliyun.com
2. 点击"创建实例"
3. 选择合适的配置

#### 步骤2：配置安全组

1. 进入ECS控制台
2. 选择您的实例 → 点击"安全组"
3. 点击"配置规则"
4. 添加以下入方向规则：
   - SSH（端口22）：允许您的IP访问
   - HTTP（端口80）：允许所有IP访问
   - HTTPS（端口443）：允许所有IP访问
   - 自定义TCP（端口8000-9000）：允许所有IP访问（后端API端口）

#### 步骤3：连接到ECS

**使用SSH连接**：
```bash
# Windows使用PowerShell或PuTTY
# Mac/Linux使用终端
ssh root@your-ecs-public-ip
```

### 2.2 环境配置

#### 步骤1：更新系统
```bash
apt update && apt upgrade -y
```

#### 步骤2：安装必要软件
```bash
# 安装Python 3.10+
apt install python3 python3-pip python3-venv -y

# 安装Nginx（用于反向代理）
apt install nginx -y

# 安装Git
apt install git -y

# 安装Supervisor（用于进程管理）
apt install supervisor -y
```

#### 步骤3：配置防火墙
```bash
# 允许HTTP和HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### 2.3 部署后端

#### 步骤1：克隆代码
```bash
cd /opt
git clone https://github.com/maco1979/ai-agriculture-system.git
cd ai-agriculture-system
git checkout clean-deploy-v2
```

#### 步骤2：创建Python虚拟环境
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### 步骤3：安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 步骤4：配置环境变量
```bash
# 创建环境变量文件
nano .env
```

添加以下内容：
```env
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-supabase-url.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
JWT_SECRET=your-secure-jwt-secret
ENVIRONMENT=production
```

保存并退出：`Ctrl+O` → `Enter` → `Ctrl+X`

#### 步骤5：测试后端
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行后端
python main.py
```

在另一个终端测试：
```bash
curl http://localhost:8001/health
```

#### 步骤6：配置Supervisor（后台运行）

创建Supervisor配置文件：
```bash
nano /etc/supervisor/conf.d/ai-agriculture-backend.conf
```

添加以下内容：
```ini
[program:ai-agriculture-backend]
directory=/opt/ai-agriculture-system/backend
command=/opt/ai-agriculture-system/backend/venv/bin/python main.py
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-agriculture-backend.err.log
stdout_logfile=/var/log/ai-agriculture-backend.out.log
environment=PYTHONUNBUFFERED="1"
```

启动服务：
```bash
supervisorctl reread
supervisorctl update
supervisorctl start ai-agriculture-backend
```

查看状态：
```bash
supervisorctl status
```

查看日志：
```bash
tail -f /var/log/ai-agriculture-backend.out.log
tail -f /var/log/ai-agriculture-backend.err.log
```

#### 步骤7：配置Nginx反向代理

创建Nginx配置文件：
```bash
nano /etc/nginx/sites-available/ai-agriculture-backend
```

添加以下内容：
```nginx
server {
    listen 80;
    server_name your-backend-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用站点：
```bash
ln -s /etc/nginx/sites-available/ai-agriculture-backend /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

测试配置：
```bash
nginx -t
```

重启Nginx：
```bash
systemctl restart nginx
systemctl enable nginx
```

### 2.4 配置SSL证书（可选但推荐）

使用Let's Encrypt免费证书：

```bash
# 安装Certbot
apt install certbot python3-certbot-nginx -y

# 获取证书
certbot --nginx -d your-backend-domain.com

# 自动续期
certbot renew --dry-run
```

## 三、数据库方案

### 方案A：继续使用Supabase（推荐）

无需更改，保持现有配置即可。

### 方案B：使用阿里云RDS PostgreSQL

1. 访问：https://rds.console.aliyun.com
2. 创建PostgreSQL实例
3. 配置白名单，允许ECS IP访问
4. 获取连接信息
5. 更新后端环境变量中的`DATABASE_URL`
6. 执行`init.sql`初始化数据库

## 四、域名配置（可选）

### 4.1 购买域名

1. 访问：https://wanwang.aliyun.com
2. 搜索并购买您喜欢的域名

### 4.2 配置DNS解析

1. 进入云解析DNS控制台：https://dns.console.aliyun.com
2. 添加域名
3. 配置解析记录：

**前端解析**：
```
记录类型：CNAME
主机记录：@ 或 www
记录值：您的CDN域名
TTL：600
```

**后端解析**：
```
记录类型：A
主机记录：api
记录值：您的ECS公网IP
TTL：600
```

## 五、成本估算

### 免费试用（新用户）
- ECS：免费3个月
- OSS：免费5GB存储空间 + 5GB流量
- CDN：免费10GB流量
- RDS：免费1个月（如需要）

### 长期使用（预估）
- ECS（2核4GB）：约 ¥100-¥200/月
- OSS：约 ¥10-¥30/月（取决于存储和流量）
- CDN：约 ¥10-¥50/月（取决于流量）
- RDS（如需要）：约 ¥100-¥200/月
- **总计**：约 ¥120-¥480/月

## 六、监控和维护

### 6.1 监控后端服务

```bash
# 查看Supervisor状态
supervisorctl status

# 查看日志
tail -f /var/log/ai-agriculture-backend.out.log

# 重启服务
supervisorctl restart ai-agriculture-backend
```

### 6.2 监控Nginx

```bash
# 查看Nginx状态
systemctl status nginx

# 查看访问日志
tail -f /var/log/nginx/access.log

# 查看错误日志
tail -f /var/log/nginx/error.log
```

### 6.3 定期备份

创建备份脚本：
```bash
nano /opt/backup.sh
```

添加内容：
```bash
#!/bin/bash
BACKUP_DIR=/opt/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库（如使用RDS）
# pg_dump -h your-rds-host -U your-user -d your-db > $BACKUP_DIR/db_$DATE.sql

# 备份代码
tar -czf $BACKUP_DIR/code_$DATE.tar.gz /opt/ai-agriculture-system

# 删除7天前的备份
find $BACKUP_DIR -type f -mtime +7 -delete
```

添加定时任务：
```bash
crontab -e
```

添加：
```
0 2 * * * /opt/backup.sh
```

## 七、故障排除

### 常见问题

1. **后端无法启动**
   - 检查Supervisor日志：`tail -f /var/log/ai-agriculture-backend.err.log`
   - 确认端口未被占用：`netstat -tlnp`
   - 确认虚拟环境正确激活

2. **Nginx 502错误**
   - 确认后端服务正在运行：`supervisorctl status`
   - 检查Nginx配置：`nginx -t`
   - 查看Nginx错误日志

3. **前端无法访问后端API**
   - 检查安全组配置
   - 确认Nginx反向代理配置正确
   - 检查CORS配置

4. **数据库连接失败**
   - 确认数据库地址、端口、用户名、密码正确
   - 检查数据库白名单配置
   - 测试网络连通性

## 八、快速启动脚本

创建一键部署脚本：

```bash
nano /opt/deploy.sh
```

添加内容：
```bash
#!/bin/bash
echo "开始部署AI农业决策系统到阿里云..."

# 更新系统
apt update && apt upgrade -y

# 安装依赖
apt install python3 python3-pip python3-venv nginx supervisor git -y

# 克隆代码
cd /opt
git clone https://github.com/maco1979/ai-agriculture-system.git
cd ai-agriculture-system
git checkout clean-deploy-v2

# 配置后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "部署完成！请配置环境变量并启动服务。"
```

使用方法：
```bash
chmod +x /opt/deploy.sh
/opt/deploy.sh
```

## 九、总结

阿里云部署方案提供了稳定、快速、低成本的部署选择。根据您的需求，可以选择：

- **最小成本方案**：OSS前端 + ECS后端 + Supabase数据库
- **全阿里云方案**：OSS前端 + ECS后端 + RDS数据库
- **高可用方案**：OSS前端 + SLB + 多台ECS + RDS主从

如有问题，请参考阿里云官方文档或联系技术支持。
