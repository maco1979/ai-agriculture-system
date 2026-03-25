# ============================================================
# AI农业决策系统 - 后端 Dockerfile
# 基于 Python 3.11（兼容 JAX/Flax，避免 3.12+ 兼容性问题）
# ============================================================

FROM python:3.11-slim AS base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ---- 依赖安装阶段 ----
FROM base AS deps

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 优先复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# ---- 生产运行阶段 ----
FROM base AS production

# 安装运行时系统依赖（精简版）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从依赖阶段复制已安装的包
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建非 root 用户（安全最佳实践）
RUN useradd -m -u 1000 -s /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

# 暴露端口（Railway/云平台会通过 $PORT 覆盖）
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# 启动命令：优先读取环境变量 PORT（Railway/云平台标准）
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
