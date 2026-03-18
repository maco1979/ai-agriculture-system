---
name: camera-ptz
description: >
  摄像头与PTZ云台控制技能 - 操控AI农业系统中的视觉感知设备。
  Use when: 用户提到摄像头、拍照、查看画面、云台、PTZ控制、
             转动摄像头、变焦、自动跟踪、作物识别/分类、视觉监控等。
  NOT for: 农业决策查询、模型管理等其他功能。
---

# 摄像头 & PTZ云台控制技能

## 说明

系统支持真实摄像头（通过 OpenCV/ONVIF/Pelco-D 连接）和**模拟模式**（无硬件时自动降级）。
模拟模式返回合法的测试图像数据，功能正常。

---

## 工作流程

1. 先获取摄像头列表，确认目标摄像头 ID
2. 若摄像头未开启，先调用开启接口
3. 执行具体操作（移动/变焦/预置位/识别等）
4. 用自然语言向用户描述操作结果

---

## 操作指令

### 📋 获取摄像头列表

```bash
python scripts/camera-control.py list
```

或 curl：
```bash
curl -s http://localhost:8001/api/camera/cameras | python -m json.tool
```

---

### ▶️ 开启/关闭摄像头

```bash
python scripts/camera-control.py start --camera cam_001
python scripts/camera-control.py stop --camera cam_001
```

---

### 🖼️ 获取当前画面

```bash
python scripts/camera-control.py frame --camera cam_001
```

（返回Base64编码图像，可保存为文件）

---

### 🎯 PTZ云台 — 方向控制

```bash
python scripts/camera-control.py ptz-move --camera cam_001 --direction left --speed 5
```

方向：`up`（上）/ `down`（下）/ `left`（左）/ `right`（右）/ `stop`（停止）
速度：1-10（1最慢，10最快）

---

### 🔍 PTZ云台 — 变焦

```bash
python scripts/camera-control.py ptz-zoom --camera cam_001 --zoom-in --speed 3
```

- `--zoom-in`：放大  
- `--zoom-out`：缩小

---

### 📌 预置位操作

```bash
# 保存当前位置为预置位1
python scripts/camera-control.py ptz-save-preset --camera cam_001 --preset 1 --name "作物区域A"

# 跳转到预置位1
python scripts/camera-control.py ptz-goto-preset --camera cam_001 --preset 1
```

---

### 🤖 自动跟踪

```bash
# 开启自动跟踪（跟踪作物目标）
python scripts/camera-control.py ptz-track --camera cam_001 --enable --target crop

# 关闭自动跟踪
python scripts/camera-control.py ptz-track --camera cam_001 --disable
```

跟踪目标类型：`crop`（作物）/ `person`（人员）/ `animal`（动物）/ `vehicle`（车辆）

---

### 🧠 视觉识别

```bash
python scripts/camera-control.py recognize --camera cam_001 --task crop_classification
```

识别任务：`crop_classification`（作物分类）/ `pest_detection`（病虫害检测）/ `growth_stage`（生长阶段判断）

---

## 硬件连接（真实PTZ云台）

```bash
# 通过ONVIF连接真实云台
curl -s -X POST http://localhost:8001/api/camera/ptz/connect \
  -H "Content-Type: application/json" \
  -d "{\"camera_id\": \"cam_001\", \"protocol\": \"ONVIF\", \"host\": \"192.168.1.100\", \"port\": 80, \"username\": \"admin\", \"password\": \"admin123\"}"
```

支持的协议：`ONVIF`、`PELCO_D`、`PELCO_P`、`VISCA`、`HTTP_API`

---

## 结果说明

- 画面帧返回 Base64 PNG，告知用户"已获取摄像头画面"
- PTZ 移动操作告知方向和速度
- 识别结果说明检测到的类别、置信度、建议操作
- 若硬件不可用，说明"当前为模拟模式，返回仿真数据"
