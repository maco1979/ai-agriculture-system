# 监控系统部署指南

## 1. 部署Jaeger（分布式追踪）

### 1.1 下载Jaeger

1. 访问 Jaeger GitHub 发布页面：https://github.com/jaegertracing/jaeger/releases
2. 下载适合您系统的版本：
   - Windows: `jaeger-x.x.x-windows-amd64.zip`
   - Linux: `jaeger-x.x.x-linux-amd64.tar.gz`
   - macOS: `jaeger-x.x.x-darwin-amd64.tar.gz`

### 1.2 安装和运行Jaeger

#### Windows
1. 解压下载的ZIP文件
2. 打开命令提示符，进入解压目录
3. 运行以下命令启动Jaeger：
   ```bash
   jaeger-all-in-one.exe
   ```

#### Linux/macOS
1. 解压下载的压缩文件
2. 打开终端，进入解压目录
3. 运行以下命令启动Jaeger：
   ```bash
   ./jaeger-all-in-one
   ```

### 1.3 访问Jaeger UI

Jaeger UI默认运行在 `http://localhost:16686`，您可以通过浏览器访问该地址查看追踪数据。

## 2. 部署Prometheus（指标收集）

### 2.1 下载Prometheus

1. 访问 Prometheus GitHub 发布页面：https://github.com/prometheus/prometheus/releases
2. 下载适合您系统的版本：
   - Windows: `prometheus-x.x.x.windows-amd64.zip`
   - Linux: `prometheus-x.x.x.linux-amd64.tar.gz`
   - macOS: `prometheus-x.x.x.darwin-amd64.tar.gz`

### 2.2 配置Prometheus

1. 解压下载的压缩文件
2. 创建 `prometheus.yml` 配置文件，内容如下：

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "ai-platform"
    static_configs:
      - targets: ["localhost:8000"]
```

### 2.3 运行Prometheus

#### Windows
1. 打开命令提示符，进入解压目录
2. 运行以下命令启动Prometheus：
   ```bash
   prometheus.exe --config.file=prometheus.yml
   ```

#### Linux/macOS
1. 打开终端，进入解压目录
2. 运行以下命令启动Prometheus：
   ```bash
   ./prometheus --config.file=prometheus.yml
   ```

### 2.4 访问Prometheus UI

Prometheus UI默认运行在 `http://localhost:9090`，您可以通过浏览器访问该地址查看指标数据。

## 3. 部署Grafana（监控仪表板）

### 3.1 下载Grafana

1. 访问 Grafana 下载页面：https://grafana.com/grafana/download
2. 下载适合您系统的版本并安装

### 3.2 配置Grafana数据源

1. 启动Grafana（默认运行在 `http://localhost:3000`）
2. 登录Grafana（默认用户名/密码：admin/admin）
3. 按照以下步骤添加Prometheus数据源：
   - 点击左侧菜单中的 "Configuration" -> "Data sources"
   - 点击 "Add data source"
   - 选择 "Prometheus"
   - 在 "HTTP" 部分，设置 "URL" 为 `http://localhost:9090`
   - 点击 "Save & Test" 验证连接

### 3.3 导入Grafana仪表板

1. 点击左侧菜单中的 "Dashboards" -> "Import"
2. 上传 `grafana_dashboard.json` 文件
3. 选择之前配置的Prometheus数据源
4. 点击 "Import" 完成导入

## 4. 配置环境变量

### 4.1 编辑 .env 文件

根据您的部署环境，编辑 `.env` 文件中的配置：

```env
# 日志配置
LOG_LEVEL=INFO

# Jaeger配置
JAEGER_HOST=localhost  # Jaeger服务地址
JAEGER_PORT=6831       # Jaeger服务端口

# 数据库配置
DATABASE_URL=postgresql://admin:password@localhost:5432/example_db

# API配置
API_PORT=8000
SECRET_KEY=your-secret-key-here

# 环境配置
ENV=development  # development 或 production
```

### 4.2 环境变量说明

- `LOG_LEVEL`：日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
- `JAEGER_HOST`：Jaeger服务的主机地址
- `JAEGER_PORT`：Jaeger服务的端口
- `DATABASE_URL`：数据库连接字符串
- `API_PORT`：API服务的端口
- `SECRET_KEY`：用于JWT签名的密钥
- `ENV`：运行环境，development（开发）或 production（生产）

## 5. 启动应用服务

### 5.1 安装依赖

```bash
pip install -r requirements.txt
```

### 5.2 启动服务

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## 6. 验证监控系统

1. **验证日志系统**：检查应用启动日志，确认日志格式是否为JSON格式
2. **验证分布式追踪**：访问API接口，然后在Jaeger UI中查看追踪数据
3. **验证指标收集**：在Prometheus UI中查看收集的指标
4. **验证Grafana仪表板**：在Grafana中查看监控仪表板，确认数据是否正常显示

## 7. 故障排查

### 7.1 Jaeger连接问题

- 确保Jaeger服务已启动
- 检查 `JAEGER_HOST` 和 `JAEGER_PORT` 配置是否正确
- 检查网络防火墙是否允许连接

### 7.2 Prometheus连接问题

- 确保Prometheus服务已启动
- 检查 `prometheus.yml` 配置是否正确
- 检查应用是否暴露了指标端点

### 7.3 Grafana仪表板问题

- 确保Grafana服务已启动
- 检查数据源配置是否正确
- 检查仪表板导入是否成功

## 8. 最佳实践

1. **生产环境部署**：
   - 使用容器化部署（Docker）
   - 配置适当的资源限制
   - 启用持久化存储

2. **监控配置**：
   - 根据业务需求添加更多监控指标
   - 设置合理的告警规则
   - 定期备份监控数据

3. **性能优化**：
   - 调整Prometheus的抓取间隔
   - 配置Jaeger的采样率
   - 优化日志级别，避免过多的DEBUG日志

## 9. 相关链接

- Jaeger官方文档：https://www.jaegertracing.io/docs/
- Prometheus官方文档：https://prometheus.io/docs/
- Grafana官方文档：https://grafana.com/docs/
- OpenTelemetry官方文档：https://opentelemetry.io/docs/