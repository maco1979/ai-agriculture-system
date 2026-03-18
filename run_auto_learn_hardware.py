#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习控制本地硬件 - 快速启动脚本
提供简单的命令行界面来运行自动学习硬件控制系统
"""

import asyncio
import sys
import os
import argparse
import json
from datetime import datetime

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from auto_learn_hardware_control import AutoLearnHardwareControlSystem


class AutoLearnHardwareCLI:
    """命令行界面"""
    
    def __init__(self):
        self.system = None
        self.running = False
    
    async def start(self, duration: int = 60, demo_mode: bool = True):
        """启动系统"""
        print("🚀 启动自动学习控制本地硬件系统...")
        print("=" * 60)
        
        self.system = AutoLearnHardwareControlSystem()
        
        try:
            # 初始化系统
            await self.system.initialize_system()
            self.running = True
            
            if demo_mode:
                # 运行演示模式
                await self.system.run_demo(duration=duration)
            else:
                # 交互模式
                await self.interactive_mode()
                
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.stop()
    
    async def interactive_mode(self):
        """交互模式"""
        print("\n🎮 进入交互模式")
        print("可用命令:")
        print("  status  - 查看系统状态")
        print("  devices - 查看设备列表")
        print("  control <device_id> <action> - 手动控制设备")
        print("  learn   - 立即执行学习")
        print("  help    - 显示帮助")
        print("  quit    - 退出系统")
        print("-" * 60)
        
        while self.running:
            try:
                command = input("\n> ").strip().lower()
                
                if command == "quit" or command == "exit":
                    break
                elif command == "status":
                    await self.show_status()
                elif command == "devices":
                    await self.show_devices()
                elif command.startswith("control "):
                    await self.handle_control(command)
                elif command == "learn":
                    await self.trigger_learning()
                elif command == "help":
                    self.show_help()
                else:
                    print("未知命令，输入 'help' 查看帮助")
                    
            except EOFError:
                break
            except Exception as e:
                print(f"错误: {e}")
    
    async def show_status(self):
        """显示系统状态"""
        if self.system:
            status = self.system.get_system_status()
            print("\n📊 系统状态:")
            print(json.dumps(status, indent=2, ensure_ascii=False))
    
    async def show_devices(self):
        """显示设备列表"""
        if self.system:
            print(f"\n📱 已发现 {len(self.system.devices)} 个设备:")
            for device in self.system.devices:
                print(f"  [{device['id']}] {device['name']} ({device.get('type', 'unknown')})")
                print(f"      状态: {'在线' if device.get('connected') else '离线'}, "
                      f"连接: {device.get('connection_type', 'unknown')}")
    
    async def handle_control(self, command: str):
        """处理控制命令"""
        parts = command.split()
        if len(parts) < 3:
            print("用法: control <device_id> <action>")
            return
        
        device_id = parts[1]
        action = parts[2]
        parameters = {}
        
        # 解析额外参数
        for i in range(3, len(parts)):
            if "=" in parts[i]:
                key, value = parts[i].split("=", 1)
                try:
                    value = float(value)
                except:
                    pass
                parameters[key] = value
        
        result = await self.system.manual_control(device_id, action, parameters)
        print(f"控制结果: {result}")
    
    async def trigger_learning(self):
        """触发学习"""
        print("\n🎓 触发学习周期...")
        # 学习循环会自动执行，这里只是显示状态
        status = self.system.get_system_status()
        print(f"学习周期: {status['learning']['learning_cycles']}")
        print(f"性能分数: {status['learning']['performance_score']:.2%}")
    
    def show_help(self):
        """显示帮助"""
        print("\n📖 帮助:")
        print("  status  - 显示系统状态")
        print("  devices - 显示设备列表")
        print("  control <device_id> <action> [param=value] - 控制设备")
        print("            示例: control 123 cool_down intensity=0.8")
        print("  learn   - 显示学习状态")
        print("  help    - 显示此帮助")
        print("  quit    - 退出系统")
    
    async def stop(self):
        """停止系统"""
        if self.system:
            print("\n🛑 停止系统...")
            await self.system.cleanup()
            self.running = False
            print("✅ 系统已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="自动学习控制本地硬件系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_auto_learn_hardware.py              # 运行60秒演示
  python run_auto_learn_hardware.py -d 120       # 运行120秒演示
  python run_auto_learn_hardware.py -i           # 交互模式
        """
    )
    
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=60,
        help="演示运行时长（秒），默认60秒"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="启用交互模式"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="自动学习控制本地硬件系统 v1.0"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 自动学习控制本地硬件系统")
    print("=" * 60)
    
    cli = AutoLearnHardwareCLI()
    
    try:
        asyncio.run(cli.start(
            duration=args.duration,
            demo_mode=not args.interactive
        ))
    except KeyboardInterrupt:
        print("\n\n⚠️ 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n👋 感谢使用!")


if __name__ == "__main__":
    main()
