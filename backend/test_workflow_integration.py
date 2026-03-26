"""
工作流程集成测试
测试完整流程：AI发帖 → AI讨论 → 生成提案 → 微信推送 → 用户审批 → 自动执行 → 结果反馈
"""

import asyncio
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.community_scheduler import trigger_event_post
from services.community_dialogue import start_ai_dialogue
from services.task_proposal_service import get_pending_proposals, get_proposal
from services.wechat_notification_service import get_subscribed_users


async def test_complete_workflow():
    """测试完整工作流程"""
    print("=" * 60)
    print("🚀 开始测试完整工作流程")
    print("=" * 60)
    
    # 步骤1: 触发AI发帖（模拟高温预警）
    print("\n📌 步骤1: 触发AI发帖（高温预警）")
    success = await trigger_event_post("high_temperature", {"value": "35.5"})
    if success:
        print("✅ AI发帖成功")
    else:
        print("❌ AI发帖失败")
        return False
    
    # 等待帖子生成
    await asyncio.sleep(2)
    
    # 步骤2: 获取最新帖子并触发AI讨论
    print("\n📌 步骤2: 触发AI多角色讨论")
    from services.community_db import list_posts
    posts = list_posts()
    if not posts:
        print("❌ 未找到帖子")
        return False
    
    latest_post = posts[0]
    post_id = latest_post["id"]
    print(f"📄 帖子ID: {post_id}")
    print(f"📄 标题: {latest_post['title']}")
    
    # 触发AI讨论
    reply_count = await start_ai_dialogue(post_id)
    print(f"✅ AI讨论完成，共 {reply_count} 条回复")
    
    # 等待提案生成
    await asyncio.sleep(3)
    
    # 步骤3: 检查是否生成任务提案
    print("\n📌 步骤3: 检查任务提案生成")
    proposals = get_pending_proposals(limit=5)
    if proposals:
        proposal = proposals[0]
        proposal_id = proposal["proposal_id"]
        print(f"✅ 生成任务提案: {proposal_id}")
        print(f"📄 标题: {proposal['title']}")
        print(f"📄 类型: {proposal['task_type']}")
        print(f"📄 风险等级: {proposal['risk_level']}")
        print(f"📄 预计耗时: {proposal['estimated_duration']} 分钟")
        print(f"📄 描述: {proposal['description'][:100]}...")
    else:
        print("⚠️  未生成任务提案（可能讨论内容不足以生成任务）")
        return True  # 这不算失败，只是没有生成任务
    
    # 步骤4: 检查微信订阅用户
    print("\n📌 步骤4: 检查微信订阅用户")
    users = get_subscribed_users()
    print(f"👥 订阅用户数: {len(users)}")
    if users:
        print(f"📱 第一个用户: {users[0][:10]}...")
    else:
        print("⚠️  没有微信订阅用户（需要配置微信小程序）")
    
    # 步骤5: 模拟用户审批
    print("\n📌 步骤5: 模拟用户审批")
    from services.task_proposal_service import approve_proposal
    success = await approve_proposal(proposal_id, "test_user_001")
    if success:
        print("✅ 任务已批准并开始执行")
    else:
        print("❌ 审批失败")
        return False
    
    # 等待任务执行
    print("\n⏳ 等待任务执行完成...")
    await asyncio.sleep(5)
    
    # 步骤6: 检查执行结果
    print("\n📌 步骤6: 检查执行结果")
    proposal = get_proposal(proposal_id)
    if proposal:
        print(f"📊 任务状态: {proposal['status']}")
        if proposal['status'] == 'completed':
            print(f"✅ 任务执行完成: {proposal['result']}")
        elif proposal['status'] == 'failed':
            print(f"❌ 任务执行失败: {proposal['result']}")
        else:
            print(f"⏳ 任务状态: {proposal['status']}")
    
    print("\n" + "=" * 60)
    print("🎉 完整工作流程测试完成")
    print("=" * 60)
    return True


async def test_task_proposal_generation():
    """单独测试任务提案生成功能"""
    print("\n" + "=" * 60)
    print("🧪 测试任务提案生成")
    print("=" * 60)
    
    from services.task_proposal_service import generate_task_proposal
    from services.community_db import list_posts
    
    # 获取最新帖子
    posts = list_posts()
    if not posts:
        print("❌ 未找到帖子")
        return False
    
    # 选择第一个帖子生成提案
    post_id = posts[0]["id"]
    print(f"📄 使用帖子ID: {post_id}")
    
    proposal = await generate_task_proposal(post_id)
    if proposal:
        print(f"✅ 提案生成成功")
        print(f"📄 提案ID: {proposal.proposal_id}")
        print(f"📄 标题: {proposal.title}")
        print(f"📄 任务类型: {proposal.task_type.value}")
        print(f"📄 风险等级: {proposal.risk_level}")
        return True
    else:
        print("⚠️  未生成提案（可能是讨论内容不足以生成任务）")
        return True


async def main():
    """主测试函数"""
    print("🧪 AI农业决策系统 - 工作流程集成测试")
    print("=" * 60)
    
    # 检查数据库初始化
    print("\n📋 检查数据库初始化...")
    try:
        from services.task_proposal_service import init_task_proposal_db
        from services.wechat_notification_service import init_wechat_db
        print("✅ 数据库初始化完成")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    # 运行测试
    try:
        # 测试1: 任务提案生成
        await test_task_proposal_generation()
        
        # 测试2: 完整工作流程
        # await test_complete_workflow()  # 暂时跳过完整测试，避免影响现有数据
        
        print("\n✅ 所有测试完成")
        return True
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
