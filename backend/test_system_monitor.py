#!/usr/bin/env python3
"""
测试系统监控服务
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
src_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(src_dir)
sys.path.append(project_root)

async def test_system_monitor():
    """测试系统监控服务"""
    print("开始测试系统监控服务...")
    
    try:
        # 导入系统监控服务
        from src.core.services import start_system_monitor, stop_system_monitor, get_system_monitor
        
        print("✓ 成功导入系统监控服务")
        
        # 启动系统监控
        print("启动系统监控服务...")
        await start_system_monitor()
        print("✓ 系统监控服务已启动")
        
        # 等待一段时间让监控服务收集数据
        await asyncio.sleep(2)
        
        # 获取系统监控实例
        monitor = get_system_monitor()
        
        # 获取当前统计信息
        current_stats = monitor.get_current_stats()
        print("✓ 获取当前统计信息成功")
        print(f"  CPU使用率: {current_stats.get('cpu', {}).get('percent', 'N/A')}%")
        print(f"  内存使用率: {current_stats.get('memory', {}).get('percent', 'N/A')}%")
        print(f"  磁盘使用率: {current_stats.get('disk', {}).get('percent', 'N/A')}%")
        
        # 获取统计摘要
        stats_summary = monitor.get_stats_summary()
        print("✓ 获取统计摘要成功")
        print(f"  CPU平均使用率: {stats_summary.get('cpu', {}).get('average', 'N/A')}%")
        print(f"  内存平均使用率: {stats_summary.get('memory', {}).get('average', 'N/A')}%")
        
        # 等待一段时间让历史数据积累
        await asyncio.sleep(3)
        
        # 获取历史数据
        cpu_history = monitor.get_history("cpu")
        memory_history = monitor.get_history("memory")
        print("✓ 获取历史数据成功")
        print(f"  CPU历史数据点: {len(cpu_history)}")
        print(f"  内存历史数据点: {len(memory_history)}")
        
        # 停止系统监控
        print("停止系统监控服务...")
        await stop_system_monitor()
        print("✓ 系统监控服务已停止")
        
        print("\n🎉 系统监控服务测试成功！")
        
    except ImportError as e:
        print(f"❌ 导入系统监控服务失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_system_monitor())