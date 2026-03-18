# AI农业决策系统 — API 完整参考

## 基础地址
`http://localhost:8001`

---

## 🌱 农业模块 `/api/agriculture`

### 生成光配方
**POST** `/api/agriculture/light-formula`
```json
{
  "crop_type": "番茄",
  "growth_stage": "开花期",
  "target_yield": "高产量"
}
```
返回：红蓝绿光比例、光照强度(PPFD)、光周期设置

### 植物生长预测
**POST** `/api/agriculture/growth-prediction`
```json
{
  "crop_type": "生菜",
  "current_stage": "苗期",
  "environment": {"temperature": 22, "humidity": 70, "light_hours": 14}
}
```

### 种植规划
**POST** `/api/agriculture/planting-plan`
```json
{"crop_type": "黄瓜", "area_sqm": 100, "start_date": "2026-03-15"}
```

### 作物建议
**GET** `/api/agriculture/crop-recommendations?season=spring&location=北京`

### 数据贡献
**POST** `/api/agriculture/data-contribution`
```json
{"crop_type": "番茄", "data": {...}, "contributor": "farm_001"}
```

---

## 📷 摄像头模块 `/api/camera`

### 获取摄像头列表
**GET** `/api/camera/cameras`

### 开启/关闭摄像头
**POST** `/api/camera/start`  |  **POST** `/api/camera/stop`
```json
{"camera_id": "cam_001"}
```

### 获取当前帧（Base64图像）
**GET** `/api/camera/frame?camera_id=cam_001`

### PTZ云台控制

#### 连接云台
**POST** `/api/camera/ptz/connect`
```json
{"camera_id": "cam_001", "protocol": "ONVIF", "host": "192.168.1.100"}
```

#### 移动方向
**POST** `/api/camera/ptz/move`
```json
{"camera_id": "cam_001", "direction": "left", "speed": 5}
```
方向值：`up` / `down` / `left` / `right` / `stop`

#### 变焦
**POST** `/api/camera/ptz/zoom`
```json
{"camera_id": "cam_001", "zoom_in": true, "speed": 3}
```

#### 预置位操作
**POST** `/api/camera/ptz/preset/save`
```json
{"camera_id": "cam_001", "preset_id": 1, "name": "作物区域A"}
```
**POST** `/api/camera/ptz/preset/goto`
```json
{"camera_id": "cam_001", "preset_id": 1}
```

#### 自动跟踪
**POST** `/api/camera/ptz/auto-track`
```json
{"camera_id": "cam_001", "enabled": true, "target_type": "crop"}
```

#### 视觉识别
**POST** `/api/camera/recognize`
```json
{"camera_id": "cam_001", "task": "crop_classification"}
```

---

## 🤖 AI模型模块 `/api/models`

### 获取模型列表
**GET** `/api/models`

### 获取模型详情
**GET** `/api/models/{model_id}`

### 启动/暂停模型
**POST** `/api/models/{model_id}/start`
**POST** `/api/models/{model_id}/pause`

### 训练模型
**POST** `/api/models/{model_id}/train`
```json
{"epochs": 10, "learning_rate": 0.001, "batch_size": 32}
```

### 执行推理
**POST** `/api/inference/execute`
```json
{
  "model_id": "resnet50_crop",
  "input_data": {"image_base64": "..."},
  "options": {}
}
```

### 推理历史
**GET** `/api/inference/history?limit=20`

---

## 🔗 区块链模块 `/api/blockchain`

### 区块链状态
**GET** `/api/blockchain/status`

### 验证模型
**POST** `/api/blockchain/verify-model`
```json
{"model_id": "organic_core", "version": "1.0.0"}
```

### 访问权限管理
**GET** `/api/blockchain/access-rights`
**POST** `/api/blockchain/grant-access`
```json
{"user_id": "farm_001", "resource": "model_data", "permission": "read"}
```

---

## 🌐 联邦学习 `/api/federated`

### 客户端注册
**POST** `/api/federated/register`
```json
{"client_id": "node_001", "data_size": 1000, "privacy_budget": 1.0}
```

### 获取当前轮次
**GET** `/api/federated/rounds/current`

### 提交结果
**POST** `/api/federated/rounds/{round_id}/submit`

---

## 📊 系统模块 `/api/system`

### 系统健康
**GET** `/api/system/health`

### 系统指标（CPU/内存/磁盘）
**GET** `/api/system/metrics`

### 系统日志
**GET** `/api/system/logs?level=INFO&limit=100`

### 更新设置
**PUT** `/api/system/settings`
```json
{"log_level": "DEBUG", "enable_metrics": true}
```

---

## 🏘️ 社区模块 `/api/community`

### 帖子列表
**GET** `/api/community/posts?category=种植技术&page=1`

### 发布帖子
**POST** `/api/community/posts`
```json
{"title": "番茄增产经验", "content": "...", "category": "种植技术"}
```

### 直播流列表
**GET** `/api/community/streams`

---

## 🧠 决策模块 `/api/decision`

### 农业决策
**POST** `/api/decision/agriculture`
```json
{
  "crop_type": "番茄",
  "growth_stage": "开花期",
  "environment_data": {"temperature": 26, "humidity": 60}
}
```

### 风险评估
**POST** `/api/decision/risk`
```json
{"scenario": "drought", "crop_type": "小麦", "region": "华北"}
```

### OrganicCore 激活/进化
**POST** `/api/decision/organic-core/activate`
**POST** `/api/decision/organic-core/evolve`

---

## ⚡ 边缘计算 `/api/edge`

### 边缘设备列表
**GET** `/api/edge/devices`

### 同步设备
**POST** `/api/edge/devices/{device_id}/sync`

---

## 🔬 JEPA-DTMPC `/api/jepa-dtmpc`

### 状态查询
**GET** `/api/jepa-dtmpc/status`

### 预测数据
**POST** `/api/jepa-dtmpc/predict`
```json
{"horizon": 24, "crop_type": "番茄", "sensor_data": {...}}
```

### 激活JEPA
**POST** `/api/jepa-dtmpc/activate`
