# ============================================================
# AI农业决策系统 - 前端 Dockerfile（多阶段构建）
# ============================================================

# ---- 构建阶段 ----
FROM node:18-alpine AS builder

WORKDIR /app

# 优先复制 package 文件（利用缓存）
COPY package*.json ./

# 安装依赖（使用 ci 保证版本锁定）
RUN npm ci

# 复制源码
COPY . .

# 构建生产版本
RUN npm run build

# ---- 生产阶段：Nginx 静态托管 ----
FROM nginx:1.25-alpine AS production

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
