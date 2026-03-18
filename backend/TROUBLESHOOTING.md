# 监控系统故障排查指南

## 1. Jaeger连接问题

### 1.1 检查Jaeger服务状态

**步骤1：确认Jaeger服务是否启动**
- **Windows**：打开任务管理器，查看是否有 `jaeger-all-in-one.exe` 进程
- **Linux/macOS**：运行 `ps aux | grep jaeger` 查看进程状态

**步骤2：检查Jaeger服务端口**
- 运行以下命令检查端口是否被占用：
  ```bash
  # Windows
  netstat -ano | findstr :6831
  
  # Linux/macOS
  lsof -i :6831
  ```

**步骤3：访问Jaeger UI**
- 在浏览器中访问 `http://localhost:16686`，确认Jaeger UI是否可以正常访问

### 1.2 检查配置

**步骤1：检查环境变量配置**
- 查看 `.env` 文件中的Jaeger配置：
  ```env
  JAEGER_HOST=localhost
  JAEGER_PORT=6831
  ```

**步骤2：检查分布式追踪服务配置**
- 查看 `src/core/services/distributed_tracing_service.py` 文件中的Jaeger配置：
  ```python
  jaeger_exporter = JaegerExporter(
      agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
      agent_port=int(os.getenv("JAEGER_PORT", "6831"))
  )
  ```

### 1.3 检查网络连接

**步骤1：测试网络连接**
- 运行以下命令测试Jaeger服务是否可访问：
  ```bash
  # Windows
  ping localhost
  
  # Linux/macOS
  ping localhost
  ```

**步骤2：测试端口连接**
- 运行以下命令测试Jaeger端口是否可访问：
  ```bash
  # Windows
  telnet localhost 6831
  
  # Linux/macOS
  nc -zv localhost 6831
  ```

**步骤3：检查防火墙设置**
- 确认防火墙是否允许6831端口的连接
- 暂时禁用防火墙测试连接

### 1.4 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Jaeger服务未启动 | Jaeger进程未运行 | 启动Jaeger服务：`jaeger-all-in-one.exe` |
| 端口被占用 | 6831端口被其他程序占用 | 查看并关闭占用端口的程序，或修改Jaeger端口 |
| 配置错误 | 环境变量配置错误 | 检查并修正 `.env` 文件中的Jaeger配置 |
| 网络连接问题 | 防火墙阻止连接 | 配置防火墙允许6831端口 |

## 2. Prometheus连接问题

### 2.1 检查Prometheus服务状态

**步骤1：确认Prometheus服务是否启动**
- **Windows**：打开任务管理器，查看是否有 `prometheus.exe` 进程
- **Linux/macOS**：运行 `ps aux | grep prometheus` 查看进程状态

**步骤2：检查Prometheus服务端口**
- 运行以下命令检查端口是否被占用：
  ```bash
  # Windows
  netstat -ano | findstr :9090
  
  # Linux/macOS
  lsof -i :9090
  ```

**步骤3：访问Prometheus UI**
- 在浏览器中访问 `http://localhost:9090`，确认Prometheus UI是否可以正常访问

### 2.2 检查配置

**步骤1：检查Prometheus配置文件**
- 查看 `prometheus.yml` 文件中的配置：
  ```yaml
  scrape_configs:
    - job_name: "ai-platform"
      static_configs:
        - targets: ["localhost:8000"]
  ```

**步骤2：检查API服务端口**
- 确认API服务是否运行在8000端口
- 检查 `.env` 文件中的 `API_PORT` 配置

### 2.3 检查指标端点

**步骤1：测试API服务是否运行**
- 在浏览器中访问 `http://localhost:8000`，确认API服务是否正常运行

**步骤2：检查指标端点**
- 在浏览器中访问 `http://localhost:8000/metrics`，确认指标端点是否可以访问

**步骤3：检查Prometheus抓取状态**
- 在Prometheus UI中，点击 "Status" -> "Targets"，查看 `ai-platform` 目标的状态

### 2.4 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Prometheus服务未启动 | Prometheus进程未运行 | 启动Prometheus服务：`prometheus.exe --config.file=prometheus.yml` |
| 配置错误 | `prometheus.yml` 配置错误 | 检查并修正配置文件中的目标地址和端口 |
| API服务未运行 | API服务未启动或端口错误 | 启动API服务并确认端口配置正确 |
| 指标端点不可访问 | 应用未暴露指标端点 | 检查应用是否正确配置了指标暴露 |

## 3. Grafana仪表板问题

### 3.1 检查Grafana服务状态

**步骤1：确认Grafana服务是否启动**
- **Windows**：打开任务管理器，查看是否有 `grafana-server.exe` 进程
- **Linux**：运行 `systemctl status grafana-server` 查看服务状态
- **macOS**：运行 `brew services list | grep grafana` 查看服务状态

**步骤2：检查Grafana服务端口**
- 运行以下命令检查端口是否被占用：
  ```bash
  # Windows
  netstat -ano | findstr :3000
  
  # Linux/macOS
  lsof -i :3000
  ```

**步骤3：访问Grafana UI**
- 在浏览器中访问 `http://localhost:3000`，确认Grafana UI是否可以正常访问

### 3.2 检查数据源配置

**步骤1：登录Grafana**
- 打开 `http://localhost:3000`
- 使用默认用户名/密码：admin/admin

**步骤2：检查Prometheus数据源**
- 点击左侧菜单中的 "Configuration" -> "Data sources"
- 确认Prometheus数据源是否存在
- 点击 "Test" 按钮测试连接

**步骤3：检查数据源URL**
- 确认数据源URL是否为 `http://localhost:9090`
- 确认Prometheus服务是否运行在该地址

### 3.3 检查仪表板导入

**步骤1：检查仪表板状态**
- 点击左侧菜单中的 "Dashboards" -> "Browse"
- 确认 `AI平台监控仪表板` 是否存在

**步骤2：重新导入仪表板**
- 点击左侧菜单中的 "Dashboards" -> "Import"
- 上传 `grafana_dashboard.json` 文件
- 选择正确的Prometheus数据源
- 点击 "Import" 完成导入

**步骤3：检查仪表板数据**
- 打开仪表板，检查各个面板是否有数据显示
- 检查时间范围设置是否正确

### 3.4 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Grafana服务未启动 | Grafana进程未运行 | 启动Grafana服务 |
| 数据源配置错误 | Prometheus地址或端口错误 | 修正数据源URL为 `http://localhost:9090` |
| 仪表板未导入 | 仪表板文件未上传 | 重新导入 `grafana_dashboard.json` 文件 |
| 无数据显示 | Prometheus未收集到数据 | 检查Prometheus配置和API服务状态 |
| 时间范围错误 | 仪表板时间范围设置不当 | 调整时间范围为合适的值 |

## 4. 综合故障排查

### 4.1 检查服务启动顺序

1. 首先启动Jaeger服务
2. 然后启动Prometheus服务
3. 接着启动Grafana服务
4. 最后启动API服务

### 4.2 检查日志

**Jaeger日志**：查看Jaeger服务的输出日志，寻找错误信息
**Prometheus日志**：查看Prometheus服务的输出日志，寻找错误信息
**Grafana日志**：查看Grafana服务的日志文件，寻找错误信息
**API服务日志**：查看API服务的输出日志，寻找关于分布式追踪和监控的错误信息

### 4.3 网络连接测试

**测试所有服务之间的连接**：
- Jaeger -> API服务：API服务向Jaeger发送追踪数据
- Prometheus -> API服务：Prometheus从API服务抓取指标
- Grafana -> Prometheus：Grafana从Prometheus查询数据

**使用curl测试连接**：
```bash
# 测试API服务
curl http://localhost:8000

# 测试指标端点
curl http://localhost:8000/metrics

# 测试Prometheus
curl http://localhost:9090

# 测试Grafana
curl http://localhost:3000
```

### 4.4 环境变量检查

**确保所有环境变量正确配置**：
- `LOG_LEVEL`：日志级别
- `JAEGER_HOST`：Jaeger服务地址
- `JAEGER_PORT`：Jaeger服务端口
- `API_PORT`：API服务端口
- `ENV`：运行环境

### 4.5 防火墙和网络设置

**检查网络设置**：
- 确保本地防火墙允许所有相关端口的连接
- 确保网络连接稳定
- 确保所有服务运行在同一网络环境中

## 5. 联系方式

如果您遇到无法解决的问题，请参考以下资源：

- Jaeger官方文档：https://www.jaegertracing.io/docs/
- Prometheus官方文档：https://prometheus.io/docs/
- Grafana官方文档：https://grafana.com/docs/
- OpenTelemetry官方文档：https://opentelemetry.io/docs/