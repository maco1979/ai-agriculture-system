# AI农业系统 API 参考

## 基础信息

- **基础URL**: `http://localhost:8001`
- **API文档**: `http://localhost:8001/docs`
- **健康检查**: `GET /health`

---

## API 端点列表

### 1. 系统监控

#### 获取系统指标
```
GET /api/system/metrics
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 38.5,
    "network_in": 1024,
    "network_out": 2048,
    "active_connections": 12,
    "uptime": "3d 5h 20m"
  }
}
```

---

### 2. AI模型管理

#### 获取模型列表
```
GET /api/models
```

#### 获取模型详情
```
GET /api/models/{model_id}
```

#### 启动模型训练
```
POST /api/models/{model_id}/train
```

**请求体**:
```json
{
  "epochs": 10,
  "batch_size": 32
}
```

#### 获取训练状态
```
GET /api/models/training/{task_id}
```

---

### 3. 农业决策

#### 获取作物配置
```
GET /api/agriculture/crop-configs
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "番茄": {
      "light_recipe": "红蓝光 3:1",
      "temperature": 25,
      "humidity": 65,
      "co2": 800
    }
  }
}
```

#### 生成光配方
```
POST /api/agriculture/light-recipe
```

**请求体**:
```json
{
  "crop_type": "番茄",
  "growth_stage": "开花期"
}
```

---

### 4. 智能体控制

#### 获取智能体状态
```
GET /api/v1/fine-tune/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "state": "idle",
    "learning_memory_size": 5,
    "decision_count": 0,
    "performance_metrics": {
      "success_rate": 1.0,
      "average_reward": 0.8
    }
  }
}
```

#### 获取学习记忆
```
GET /api/v1/fine-tune/memory?limit=10
```

#### 模拟添加记忆
```
POST /api/v1/fine-tune/memory/simulate?count=5
```

---

### 5. 摄像头控制

#### 打开摄像头
```
POST /api/camera/open
```

#### 关闭摄像头
```
POST /api/camera/close
```

#### 获取图像帧
```
GET /api/camera/frame
```

#### PTZ云台控制
```
POST /api/camera/ptz/move
```

**请求体**:
```json
{
  "pan": 10,
  "tilt": 0
}
```

---

### 6. 边缘设备

#### 获取设备列表
```
GET /api/edge/devices
```

---

### 7. 区块链

#### 获取链状态
```
GET /api/blockchain/status
```

---

### 8. 联邦学习

#### 获取学习状态
```
GET /api/federated/status
```

---

## 错误处理

所有API返回统一格式:

```json
{
  "success": false,
  "error": "错误信息"
}
```

常见HTTP状态码:
- `200` - 成功
- `404` - 资源不存在
- `500` - 服务器错误
