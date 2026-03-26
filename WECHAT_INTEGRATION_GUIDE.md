# 微信集成配置指南

## 📱 微信 ClawBot 集成（推荐）

### 一、前提条件

在开始之前，请确保您已满足以下条件：

- ✅ 已在电脑上安装并登录 WorkBuddy >= 4.6.4
- ✅ 手机上已登录一个可正常使用的微信 >= 8.0

> **提示**：微信 ClawBot 接入无需填写 App ID、App Secret 等开发凭证，只需扫码即可完成绑定。

---

### 二、打开微信 ClawBot 集成

#### 1）进入 Claw 设置

1. 打开 WorkBuddy
2. 在左侧 Claw 栏点击齿轮图标，进入「Claw 设置」

![Claw设置入口](https://github.com/user-attachments/assets/claw-settings-entry)

#### 2）配置微信集成

1. 在集成列表中找到「微信 ClawBot 集成」
2. 点击右侧的「配置」按钮

![微信集成配置](https://github.com/user-attachments/assets/wechat-integration-config)

#### 3）等待二维码生成

点击「配置」后，按钮会短暂显示为「绑定中...」，WorkBuddy 正在生成用于绑定的二维码。

![生成二维码](https://github.com/user-attachments/assets/qr-code-generating)

---

### 三、扫码完成绑定

#### 1）使用微信扫描二维码

二维码生成后会直接显示在卡片下方。打开手机微信，扫描该二维码即可完成绑定。

![扫描二维码](https://github.com/user-attachments/assets/scan-qr-code)

> **注意**：二维码有时效限制。如果二维码过期或扫码失败，请重新点击「配置」生成新的二维码。

#### 2）确认绑定成功

扫码完成后，卡片状态会变为「已绑定」。如果后续需要更换账号，可以点击「解绑」后重新绑定。

![绑定成功](https://github.com/user-attachments/assets/binding-success)

---

### 四、在系统中启用微信通知

绑定微信账号后，需要在系统中配置微信通知功能：

#### 1）修改配置文件

编辑 `backend/src/services/wechat_notification_service.py`：

```python
# 启用 ClawBot 模式
USE_CLAW_BOT = True

# ClawBot Webhook 地址（WorkBuddy自动生成）
CLAW_BOT_WEBHOOK = "http://localhost:5678/webhook/wechat"
```

#### 2）配置任务推送

编辑 `.env` 文件，添加：

```env
# 启用微信通知
WECHAT_NOTIFICATIONS_ENABLED=true

# 通知接收人（你的微信昵称）
WECHAT_RECIPIENT=你的微信昵称

# 是否推送任务提案
WECHAT_PUSH_PROPOSALS=true

# 是否推送执行结果
WECHAT_PUSH_RESULTS=true
```

---

### 五、开始使用

绑定完成后，您就可以直接在微信里和 WorkBuddy 对话，例如：

#### 1）接收任务通知

当 AI 生成任务提案时，会自动推送到微信：

```
🌾 AI农业决策系统

新任务提案：
📋 标题：高温预警 - 自动灌溉建议
🏷️ 类型：灌溉任务
⚠️ 风险：中等
⏱️ 预计：30分钟

💡 预期效果：降低作物高温胁迫，节约用水20%

👉 [点击查看详情并审批]
```

#### 2）审批任务

直接在微信中回复：

- 发送「批准」或「同意」→ 任务开始执行
- 发送「拒绝」或「不同意」→ 任务被取消
- 发送「查看详情」→ 获取任务详细信息

#### 3）查询任务状态

发送消息：

```
查询今天的任务
```

系统回复：

```
📊 今日任务统计

✅ 已完成：3个
🚀 执行中：1个
⏳ 待审批：2个

详情：
1. 灌溉任务 - 已完成（12:30）
2. 施肥任务 - 已完成（14:15）
3. 病虫害防治 - 已完成（16:00）
4. 高温预警灌溉 - 执行中（剩余15分钟）
```

#### 4）主动控制

发送指令：

```
立即执行灌溉任务
```

或

```
停止当前任务
```

WorkBuddy 会在电脑上自动执行任务，并把执行过程和最终结果同步回微信聊天窗口。

---

### 六、高级功能

#### 1）自定义通知模板

编辑 `backend/src/services/wechat_notification_service.py`：

```python
# 任务提案通知模板
def get_proposal_notification_template(proposal):
    return f"""
🌾 AI农业决策系统

新任务提案：
📋 标题：{proposal.title}
🏷️ 类型：{proposal.task_type}
⚠️ 风险：{proposal.risk_level}
⏱️ 预计：{proposal.estimated_duration}分钟

💡 {proposal.expected_outcome}

👉 回复"批准"执行任务，或"拒绝"取消
"""
```

#### 2）批量推送

如果有多个用户订阅，可以批量推送：

```python
from src.services.wechat_notification_service import send_task_proposal_notification

# 获取所有订阅用户
users = get_subscribed_users()

# 批量推送
for openid in users:
    await send_task_proposal_notification(
        openid=openid,
        proposal_title=proposal.title,
        proposal_desc=proposal.description,
        task_type=proposal.task_type.value,
        risk_level=proposal.risk_level,
    )
```

#### 3）定时报告

设置每日定时发送农场报告：

```python
# 在 community_scheduler.py 中添加
async def _daily_report_loop():
    """每日定时发送报告"""
    while True:
        now = datetime.now()
        if now.hour == 18 and now.minute == 0:  # 每天18:00
            await send_daily_report()
        await asyncio.sleep(60)
```

---

### 七、故障排除

#### 问题1：二维码无法生成

**现象**：点击「配置」后一直显示「绑定中...」

**解决**：
```bash
# 检查WorkBuddy服务
# 确保Claw服务已启动
# 查看日志
```

#### 问题2：扫码后无反应

**现象**：扫码后状态未变为「已绑定」

**解决**：
1. 检查手机网络连接
2. 确认微信版本 >= 8.0
3. 重新生成二维码
4. 检查WorkBuddy日志

#### 问题3：收不到通知

**现象**：任务生成后微信未收到推送

**解决**：
```bash
# 检查配置
cat backend/src/services/wechat_notification_service.py | grep USE_CLAW_BOT

# 检查网络
curl http://localhost:5678/webhook/wechat

# 查看日志
tail -f backend/logs/app.log
```

#### 问题4：响应延迟

**现象**：发送指令后很久才收到回复

**解决**：
- 检查电脑性能（CPU/内存）
- 优化AI模型响应速度
- 考虑使用更快的API（如DeepSeek）

---

### 八、安全建议

1. **保护Webhook地址**：不要将ClawBot webhook地址公开
2. **验证消息来源**：确保消息来自已绑定的微信账号
3. **权限控制**：敏感操作需要二次确认
4. **日志审计**：记录所有微信交互操作

---

### 九、与传统方式对比

| 功能 | 传统微信小程序开发 | ClawBot集成 |
|------|-------------------|------------|
| 开发门槛 | 需要学习小程序开发 | 无需开发 |
| AppID/AppSecret | 需要申请和配置 | 不需要 |
| 服务器域名 | 需要配置白名单 | 不需要 |
| HTTPS证书 | 需要 | 不需要 |
| 消息推送 | 需要配置模板消息 | 直接使用 |
| 开发周期 | 1-2周 | 5分钟 |
| 维护成本 | 高 | 极低 |

---

### 十、相关文档

- [ClawBot 官方文档](https://workbuddy.clawbot.com)
- [任务提案工作流](WORKFLOW_INTEGRATION_GUIDE.md)
- [API文档](http://localhost:8000/docs)

---

### 十一、快速测试

绑定完成后，可以快速测试：

```bash
# 发送测试消息
curl -X POST http://localhost:5678/webhook/wechat \
  -H "Content-Type: application/json" \
  -d '{"message": "测试", "user": "你的微信昵称"}'
```

在微信中应该收到：
```
🌾 AI农业决策系统

✅ 系统测试成功！
当前时间：2026-03-26 09:15

系统运行正常，可以接收任务通知。
```

---

**🎉 完成！** 现在您的AI农业决策系统已集成微信通知功能，可以实时接收任务推送和审批通知了！
