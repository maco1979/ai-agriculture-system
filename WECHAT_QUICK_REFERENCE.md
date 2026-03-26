# 微信集成快速参考

## 🚀 5分钟快速集成（ClawBot方式）

### 步骤1: 安装WorkBuddy
```bash
# 下载并安装 WorkBuddy >= 4.6.4
# 官网：https://workbuddy.clawbot.com
```

### 步骤2: 绑定微信账号
```bash
# 1. 打开WorkBuddy
# 2. 左侧Claw栏 → 点击齿轮图标
# 3. 找到"微信ClawBot集成" → 点击"配置"
# 4. 手机微信扫描二维码
# 5. 等待状态变为"已绑定" ✅
```

### 步骤3: 配置系统（2行）

编辑 `.env` 文件：

```env
# 启用ClawBot模式
USE_CLAW_BOT=true

# 接收通知的微信昵称
WECHAT_RECIPIENT=你的微信昵称
```

### 步骤4: 测试

```bash
# 启动后端
cd backend
python main.py

# 发送测试消息（在另一个终端）
python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from services.wechat_notification_service import send_test_message_to_wechat
asyncio.run(send_test_message_to_wechat())
"
```

检查微信是否收到测试消息 ✅

---

## 💡 使用场景示例

### 场景1: AI生成任务后自动推送

```
微信收到：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌾 AI农业决策系统

📋 新任务提案
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 高温预警 - 自动灌溉建议

🏷️ 任务类型：灌溉任务
⚠️ 风险等级：中等

💡 预期效果：降低作物高温胁迫，节约用水20%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回复以下指令：
👉 "批准" - 立即执行此任务
👉 "拒绝" - 取消此任务
👉 "详情" - 查看完整信息
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

你回复： **"批准"**

系统自动执行灌溉任务，完成后推送结果：

```
📊 任务执行结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 高温预警 - 自动灌溉建议

📈 执行结果：灌溉完成，4号田块已灌溉30分钟

⏰ 完成时间：2026-03-26 15:30

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回复：
👉 "历史" - 查看任务历史
👉 "统计" - 查看今日统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 场景2: 主动查询

你发送： **"今天的任务"**

系统回复：

```
📊 今日任务统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 已完成：3个
🚀 执行中：1个
⏳ 待审批：2个

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

最近完成的任务：
1. ✅ 灌溉任务（12:30）
2. ✅ 施肥任务（14:15）
3. ✅ 病虫害防治（16:00）

执行中：
4. 🚀 高温预警灌溉（剩余15分钟）

待审批：
5. ⏳ 明日施肥计划
6. ⏳ 土壤湿度监测
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 场景3: 主动控制

你发送： **"立即给3号田浇水10分钟"**

系统回复：

```
🚀 任务已创建
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 标题：手动灌溉任务
🏷️ 类型：灌溉
⏱️ 预计：10分钟

📍 位置：3号田块
💧 时长：10分钟

👉 回复"确认"执行，或"取消"撤销
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

你回复： **"确认"**

任务立即开始执行...

---

## 🔧 高级配置

### 自定义消息模板

编辑 `wechat_notification_service.py`：

```python
def _build_proposal_message(title, description, task_type, risk_level):
    return f"""
🌾 你的农场名称

📋 新任务：{title}

💡 {description}

👉 回复"是"执行，"否"取消
"""
```

### 添加更多指令

在 `task_proposal_service.py` 中：

```python
# 在 approve_proposal 函数中添加
if message.lower() in ["批准", "同意", "是", "yes"]:
    await approve_proposal(proposal_id, user)
elif message.lower() in ["拒绝", "不同意", "否", "no"]:
    await reject_proposal(proposal_id, user, "用户拒绝")
```

---

## 📋 支持的指令

| 指令 | 功能 |
|------|------|
| 批准 / 同意 / 是 | 批准并执行任务 |
| 拒绝 / 不同意 / 否 | 拒绝任务 |
| 详情 | 查看任务详细信息 |
| 今天的任务 | 查看今日任务统计 |
| 历史 | 查看任务历史 |
| 统计 | 查看数据分析 |
| 帮助 / ? | 显示帮助信息 |

---

## 📚 完整文档

- **详细指南**: `WECHAT_INTEGRATION_GUIDE.md`
- **工作流集成**: `WORKFLOW_INTEGRATION_GUIDE.md`
- **API文档**: http://localhost:8000/docs
- **任务管理API**: `/api/tasks/*`

---

## 🆘 故障排除

### 问题：收不到消息

**检查步骤：**

1. WorkBuddy是否运行？
   ```bash
   # 访问 http://localhost:5678 检查
   ```

2. 是否已绑定微信？
   ```bash
   # 在WorkBuddy设置中查看状态
   ```

3. 配置是否正确？
   ```bash
   # 检查 .env 文件
   cat .env | grep WECHAT
   ```

4. 测试连接
   ```bash
   cd backend
   python -c "
   import asyncio
   import sys
   sys.path.insert(0, 'src')
   from services.wechat_notification_service import test_clawbot_connection
   asyncio.run(test_clawbot_connection())
   "
   ```

### 问题：消息延迟

**解决方案：**
- 检查网络连接
- 优化后端响应速度
- 使用更快的AI模型（推荐DeepSeek）

---

## 🎯 最佳实践

1. **及时审批**：收到任务通知后30分钟内审批
2. **定期查看**：每天查看任务历史和统计
3. **反馈优化**：根据执行结果调整AI策略
4. **安全设置**：敏感操作开启二次确认

---

**🎉 完成！** 您的AI农业决策系统已集成微信通知功能，随时随地管理农场任务！
