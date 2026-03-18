---
name: system-monitor
description: >
  系统监控与区块链溯源技能 - 监控AI农业平台运行状态，管理Hyperledger Fabric区块链，
  以及操控联邦学习服务。
  Use when: 用户询问系统CPU/内存/磁盘、服务健康状态、系统日志、系统设置、
             区块链状态/模型溯源/数据溯源/访问权限、联邦学习客户端/轮次/聚合，
             或提到"区块链"、"溯源"、"联邦"、"系统状态"、"健康检查"等关键词。
  NOT for: 农业决策（用agriculture技能）、摄像头控制（用camera-ptz技能）、模型推理（用ai-models技能）。
---

# 系统监控 & 区块链溯源技能

## 模块概览

| 子模块 | 路由前缀 | 主要功能 |
|--------|---------|---------|
| 📊 系统监控 | `/api/system` | CPU/内存/磁盘指标、健康检查、日志、设置 |
| 🔗 区块链溯源 | `/api/blockchain` | 模型上链/验证/历史、数据溯源、联邦轮次记录 |
| 🌐 联邦学习 | `/api/federated` | 客户端注册、训练轮次管理、模型聚合 |
| ⚡ 性能监控 | `/api/performance` | 性能摘要、告警、基准测试、自动优化 |

> **区块链说明**：后端集成 Hyperledger Fabric 2.5。若 Fabric 节点未运行，系统自动降级为
> 模拟模式（返回随机区块数据），功能界面正常，但链上数据为仿真。

---

## 工作流程

1. 用户提问后，判断属于哪个子模块
2. 调用对应脚本或 curl 命令
3. 用友好的中文摘要解释结果；若有异常，给出排查建议

---

## ── 📊 系统监控 ──────────────────────────────

### 系统健康检查

```bash
python scripts/sysmon.py health
```

返回：服务状态、JAX/Flax 组件可用性、模型目录状态

---

### 系统资源指标（CPU / 内存 / 磁盘）

```bash
python scripts/sysmon.py metrics
```

或 curl：
```bash
curl -s http://localhost:8001/api/system/metrics | python -m json.tool
```

---

### 系统详细信息（平台 / Python版本 / 主机名）

```bash
curl -s http://localhost:8001/api/system/info | python -m json.tool
```

---

### 系统日志

```bash
python scripts/sysmon.py logs --level INFO --limit 50
```

日志级别：`DEBUG` / `INFO` / `WARNING` / `ERROR`

---

### 更新系统设置

```bash
curl -s -X PUT http://localhost:8001/api/system/settings \
  -H "Content-Type: application/json" \
  -d "{\"log_level\": \"DEBUG\", \"enable_metrics\": true}" | python -m json.tool
```

---

## ── 🔗 区块链溯源 ──────────────────────────────

### 区块链网络状态

```bash
python scripts/blockchain.py status
```

返回：网络状态、最新区块编号、交易数量、时间戳

---

### 注册 AI 模型到区块链

```bash
python scripts/blockchain.py register-model \
  --model-id organic_core \
  --version "1.0.0" \
  --description "PPO自演化农业决策模型"
```

直接 curl：
```bash
curl -s -X POST http://localhost:8001/api/blockchain/models/register \
  -H "Content-Type: application/json" \
  -d "{\"model_id\": \"organic_core\", \"model_bytes\": \"model_v1.0\", \"metadata\": {\"version\": \"1.0.0\"}}"
```

---

### 验证模型完整性

```bash
python scripts/blockchain.py verify-model --model-id organic_core --hash "abc123def456"
```

---

### 查看模型版本历史

```bash
python scripts/blockchain.py model-history --model-id organic_core
```

---

### 记录数据溯源

```bash
python scripts/blockchain.py record-provenance \
  --data-id dataset_001 \
  --model-id organic_core \
  --operation training
```

操作类型：`training`（训练数据使用）/ `inference`（推理数据使用）

---

### 查询数据溯源记录

```bash
python scripts/blockchain.py get-provenance --data-id dataset_001
```

---

### 访问权限管理

```bash
# 查看访问权限
curl -s http://localhost:8001/api/blockchain/access-rights | python -m json.tool

# 授予权限
curl -s -X POST http://localhost:8001/api/blockchain/grant-access \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"farm_001\", \"resource\": \"model_data\", \"permission\": \"read\"}"
```

---

## ── 🌐 联邦学习管理 ──────────────────────────────

### 查看所有客户端

```bash
python scripts/federated.py clients
```

---

### 注册新客户端

```bash
python scripts/federated.py register \
  --client-id node_beijing_01 \
  --data-size 5000 \
  --privacy-budget 1.0
```

---

### 开始训练轮次

```bash
python scripts/federated.py start-round \
  --model-id organic_core \
  --min-clients 2 \
  --rounds 5
```

---

### 提交客户端模型更新

```bash
python scripts/federated.py submit-update \
  --round-id round_001 \
  --client-id node_beijing_01
```

---

### 聚合当前轮次

```bash
python scripts/federated.py aggregate --round-id round_001
```

---

### 隐私配置

```bash
curl -s -X PUT http://localhost:8001/api/federated/privacy \
  -H "Content-Type: application/json" \
  -d "{\"epsilon\": 1.0, \"delta\": 1e-5, \"mechanism\": \"gaussian\"}" | python -m json.tool
```

---

## ── ⚡ 性能监控 ──────────────────────────────

### 性能摘要

```bash
curl -s http://localhost:8001/api/performance/summary | python -m json.tool
```

### 性能告警

```bash
curl -s http://localhost:8001/api/performance/alerts | python -m json.tool
```

### 触发基准测试

```bash
curl -s -X POST http://localhost:8001/api/performance/benchmark | python -m json.tool
```

### 自动优化

```bash
curl -s -X POST http://localhost:8001/api/performance/optimize | python -m json.tool
```

---

## 结果解读规则

| 指标 | 正常范围 | 建议操作 |
|------|---------|---------|
| CPU 使用率 | < 80% | > 80% 时暂停非关键模型训练 |
| 内存使用率 | < 85% | > 85% 时重启服务释放内存 |
| 磁盘使用率 | < 90% | > 90% 时清理日志和旧检查点 |
| 区块链状态 | `running` | 其他状态需检查 Fabric 节点 |
| 联邦客户端数 | ≥ 2 | 少于2个无法开始有效联邦训练 |
