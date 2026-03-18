# Prometheus安装指南

## 1. 下载Prometheus

1. 访问 Prometheus GitHub 发布页面：https://github.com/prometheus/prometheus/releases
2. 下载适合Windows系统的版本：`prometheus-2.53.0.windows-amd64.zip`

## 2. 安装Prometheus

1. **解压下载的ZIP文件**：
   - 右键点击ZIP文件，选择 "提取所有..."
   - 选择一个合适的目录，如 `D:\prometheus`

2. **验证文件结构**：
   解压后应该看到以下文件：
   - `prometheus.exe` - Prometheus主程序
   - `prometheus.yml` - 默认配置文件
   - `LICENSE` - 许可证文件
   - `NOTICE` - 通知文件

## 3. 配置Prometheus

1. **复制配置文件**：
   - 将 `d:\1.6\1.5\backend\prometheus.yml` 文件复制到Prometheus安装目录
   - 替换默认的 `prometheus.yml` 文件

2. **验证配置**：
   确保配置文件内容如下：
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

## 4. 运行Prometheus

### 方法1：直接运行
1. **打开命令提示符**：
   - 按下 `Win + R`，输入 `cmd`，按 Enter

2. **导航到Prometheus目录**：
   ```bash
   cd D:\prometheus
   ```

3. **启动Prometheus**：
   ```bash
   prometheus.exe --config.file=prometheus.yml
   ```

### 方法2：创建快捷方式
1. **创建批处理文件**：
   - 在Prometheus目录中创建 `start_prometheus.bat` 文件
   - 内容如下：
     ```batch
     @echo off
     cd /d "D:\prometheus"
     prometheus.exe --config.file=prometheus.yml
     pause
     ```

2. **运行批处理文件**：
   - 双击 `start_prometheus.bat` 文件

## 5. 验证Prometheus启动

1. **检查服务状态**：
   - 运行命令检查端口：
     ```bash
     netstat -ano | findstr :9090
     ```
   - 应该看到类似以下输出：
     ```
     TCP    0.0.0.0:9090           0.0.0.0:0              LISTENING       12345
     ```

2. **访问Prometheus UI**：
   - 在浏览器中访问：`http://localhost:9090`
   - 应该看到Prometheus的Web界面

3. **检查目标状态**：
   - 在Prometheus UI中，点击 "Status" -> "Targets"
   - 确认 `ai-platform` 目标的状态为 "UP"

## 6. 故障排查

### 错误：prometheus.exe 未被识别

**原因**：系统找不到 `prometheus.exe` 文件

**解决方案**：
1. 确认Prometheus已正确下载和解压
2. 确认当前工作目录是Prometheus安装目录
3. 使用完整路径运行：
   ```bash
   D:\prometheus\prometheus.exe --config.file=D:\prometheus\prometheus.yml
   ```

### 错误：端口9090被占用

**原因**：其他程序正在使用9090端口

**解决方案**：
1. 查找占用端口的程序：
   ```bash
   netstat -ano | findstr :9090
   ```
2. 关闭占用端口的程序，或修改Prometheus配置使用其他端口

### 错误：无法抓取ai-platform指标

**原因**：API服务未运行或配置错误

**解决方案**：
1. 确认API服务正在运行：`netstat -ano | findstr :8000`
2. 访问 `http://localhost:8000/metrics` 确认指标端点可访问
3. 检查防火墙是否允许Prometheus访问8000端口

## 7. 相关资源

- Prometheus官方文档：https://prometheus.io/docs/
- Prometheus配置文档：https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- Prometheus查询语言：https://prometheus.io/docs/prometheus/latest/querying/basics/