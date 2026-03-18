---
name: ai-models
description: >
  AI模型管理与推理技能 - 管理农业AI平台中的7个核心AI模型，执行推理任务。
  Use when: 用户询问AI模型状态、启动/暂停模型、训练模型、执行推理、
             查看推理历史、提到 PPO/ResNet/MAML/TimesNet/LightGBM/JEPA/ICM 等模型名称，
             或询问"模型"、"推理"、"训练"等关键词。
  NOT for: 农业决策建议（用agriculture技能）、摄像头控制（用camera-ptz技能）。
---

# AI模型管理与推理技能

## 内置AI模型（共7个）

| 模型ID | 名称 | 类型 | 用途 |
|--------|------|------|------|
| `organic_core` | OrganicAICore | PPO强化学习 | 自演化农业策略决策 |
| `advanced_core` | PatchTST | Transformer时序 | 农业时序预测 |
| `vision_model` | ResNet50 | 计算机视觉 | 作物图像分类(10类) |
| `meta_learning` | MAML | 元学习 | 少样本快速适应 |
| `curiosity_model` | ICM | 好奇心探索 | 强化学习探索驱动 |
| `risk_model` | LightGBM | 梯度提升 | 农业风险评估 |
| `timeseries` | TimesNet | 时序预测 | 72小时生长预测 |

---

## 工作流程

1. 先获取模型列表确认模型ID
2. 根据用户需求选择操作：查看/启动/训练/推理
3. 展示结果时，用非技术语言解释模型输出的含义

---

## 操作指令

### 📋 查看所有模型

```bash
python scripts/model-manager.py list
```

或：
```bash
curl -s http://localhost:8001/api/models | python -m json.tool
```

---

### 🔍 查看模型详情

```bash
python scripts/model-manager.py info --model organic_core
```

---

### ▶️ 启动 / ⏸ 暂停模型

```bash
python scripts/model-manager.py start --model organic_core
python scripts/model-manager.py pause --model risk_model
```

---

### 🏋️ 训练模型

```bash
python scripts/model-manager.py train --model vision_model --epochs 10 --lr 0.001
```

---

### 🧠 执行推理

```bash
# 风险评估推理
python scripts/model-manager.py infer --model risk_model \
  --input "{\"crop_type\": \"番茄\", \"temperature\": 35, \"humidity\": 30}"

# 作物图像分类（需提供base64图像）
python scripts/model-manager.py infer --model vision_model \
  --input "{\"image_base64\": \"...\"}"

# 时序生长预测
python scripts/model-manager.py infer --model timeseries \
  --input "{\"horizon\": 72, \"crop_type\": \"生菜\", \"history\": []}"
```

---

### 📜 推理历史

```bash
python scripts/model-manager.py history --limit 10
```

---

### 🔬 JEPA-DTMPC 融合预测

```bash
# 查看JEPA状态
curl -s http://localhost:8001/api/jepa-dtmpc/status | python -m json.tool

# 执行预测
curl -s -X POST http://localhost:8001/api/jepa-dtmpc/predict \
  -H "Content-Type: application/json" \
  -d "{\"horizon\": 24, \"crop_type\": \"番茄\", \"sensor_data\": {}}" | python -m json.tool

# 激活JEPA
curl -s -X POST http://localhost:8001/api/jepa-dtmpc/activate | python -m json.tool
```

---

### 🔄 OrganicCore 自演化控制

```bash
# 激活自演化核心
curl -s -X POST http://localhost:8001/api/decision/organic-core/activate | python -m json.tool

# 触发进化迭代
curl -s -X POST http://localhost:8001/api/decision/organic-core/evolve | python -m json.tool
```

---

## 结果解读规则

- **模型状态**：`running`→运行中，`paused`→已暂停，`training`→训练中，`idle`→空闲
- **推理置信度**：>0.8 高置信，0.5-0.8 中等，<0.5 建议人工确认
- **训练进度**：每轮损失值下降表示正常学习，若损失不收敛建议调整学习率
- **JEPA预测**：输出未来N小时的预测曲线，重点关注异常波动区间
