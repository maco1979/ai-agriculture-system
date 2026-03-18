---
name: agriculture
description: >
  智慧农业决策技能 - 为用户提供AI驱动的农业生产决策支持。
  Use when: 用户询问作物种植、光配方、生长预测、施肥方案、种植规划、病虫害建议、
             农业环境调控等任何与农业生产相关的问题。
  NOT for: 非农业领域查询，摄像头/模型管理等其他系统操作。
---

# 农业决策技能

## 工作流程

1. **理解用户意图**：判断用户需要哪类农业支持（光配方/生长预测/种植规划/决策建议）
2. **收集必要参数**：若用户未提供，主动询问作物类型和生长阶段
3. **调用对应API**：执行下面的命令获取AI建议
4. **解读并呈现结果**：将技术数据转化为用户友好的农业建议

---

## 操作指令

### 🌞 获取光配方（LED光谱调控）

```bash
python scripts/agriculture-api.py light-formula --crop 番茄 --stage 开花期
```

直接 curl：
```bash
curl -s -X POST http://localhost:8001/api/agriculture/light-formula \
  -H "Content-Type: application/json" \
  -d "{\"crop_type\": \"{{crop_type}}\", \"growth_stage\": \"{{stage}}\"}" | python -m json.tool
```

**支持的作物**：番茄、生菜、黄瓜、草莓、辣椒（以及任何用户指定的作物）  
**生长阶段**：苗期、营养生长期、开花期、结果期

---

### 📈 植物生长预测（72小时预测）

```bash
python scripts/agriculture-api.py predict --crop 生菜 --stage 苗期 --temp 22 --humidity 70
```

或 curl：
```bash
curl -s -X POST http://localhost:8001/api/agriculture/growth-prediction \
  -H "Content-Type: application/json" \
  -d "{\"crop_type\": \"{{crop}}\", \"current_stage\": \"{{stage}}\", \"environment\": {\"temperature\": {{temp}}, \"humidity\": {{humidity}}, \"light_hours\": {{light}}}"
```

---

### 📋 种植规划

```bash
curl -s -X POST http://localhost:8001/api/agriculture/planting-plan \
  -H "Content-Type: application/json" \
  -d "{\"crop_type\": \"{{crop}}\", \"area_sqm\": {{area}}, \"start_date\": \"{{date}}\"}" | python -m json.tool
```

---

### 🧠 AI农业决策（综合建议）

```bash
curl -s -X POST http://localhost:8001/api/decision/agriculture \
  -H "Content-Type: application/json" \
  -d "{\"crop_type\": \"{{crop}}\", \"growth_stage\": \"{{stage}}\", \"environment_data\": {\"temperature\": {{temp}}, \"humidity\": {{humidity}}}}" | python -m json.tool
```

---

### ⚠️ 风险评估

```bash
curl -s -X POST http://localhost:8001/api/decision/risk \
  -H "Content-Type: application/json" \
  -d "{\"scenario\": \"{{risk_type}}\", \"crop_type\": \"{{crop}}\", \"region\": \"{{region}}\"}" | python -m json.tool
```

风险类型：`drought`（干旱）、`flood`（洪涝）、`frost`（霜冻）、`pest`（病虫害）

---

### 🌾 作物推荐

```bash
curl -s "http://localhost:8001/api/agriculture/crop-recommendations?season={{season}}&location={{location}}" | python -m json.tool
```

季节：`spring`、`summer`、`autumn`、`winter`

---

## 结果解读规则

- **光配方返回值**：以"红光X%、蓝光Y%、绿光Z%，推荐光强N PPFD，光周期M小时"格式呈现
- **生长预测**：说明预期生长速度、关键节点、潜在风险
- **种植规划**：列出关键时间节点、操作事项、注意事项
- **决策建议**：优先级排序，给出"立即行动"和"未来建议"两类

## 常见问题处理

| 情况 | 处理方式 |
|------|---------|
| 用户未说明作物类型 | 询问："请问是什么作物？" |
| 返回500错误 | 告知系统模拟数据模式可能异常，建议重启：`python d:/1.6/1.5/backend/simple_api.py` |
| 用户需要传感器实时数据 | 说明需要摄像头或传感器在线，推荐使用camera技能采集 |
