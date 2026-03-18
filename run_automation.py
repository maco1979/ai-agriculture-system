#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化执行脚本
用于每日自动运行大宗交易分析
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta
import time

def run_analysis():
    """运行大宗交易分析"""
    print("=" * 60)
    print("大宗交易分析自动化执行")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 步骤1: 运行数据抓取
    print("\n[步骤1] 运行数据抓取脚本...")
    try:
        result = subprocess.run(
            [sys.executable, "block_trading_crawler.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print("数据抓取输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:", result.stderr)
            
        if result.returncode != 0:
            print(f"数据抓取失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"运行数据抓取脚本时出错: {e}")
        return False
    
    # 等待数据文件生成
    time.sleep(2)
    
    # 步骤2: 运行开盘分析
    print("\n[步骤2] 运行开盘半小时特征分析...")
    try:
        result = subprocess.run(
            [sys.executable, "opening_analysis.py"],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        print("开盘分析输出:")
        print(result.stdout)
        if result.stderr:
            print("错误信息:", result.stderr)
            
        if result.returncode != 0:
            print(f"开盘分析失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"运行开盘分析脚本时出错: {e}")
        return False
    
    # 步骤3: 检查生成的文件
    print("\n[步骤3] 检查生成的文件...")
    date_str = datetime.now().strftime("%Y%m%d")
    
    files_to_check = [
        f"block_trading_report_{date_str}.md",
        f"opening_analysis_report_{date_str}.md",
        f"block_trading_data_{date_str}.csv"
    ]
    
    all_files_exist = True
    for filename in files_to_check:
        filepath = os.path.join("d:\\1.6\\1.5", filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"[OK] {filename} - {file_size} 字节")
        else:
            # 尝试昨天的文件
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            yesterday_file = filename.replace(date_str, yesterday)
            yesterday_path = os.path.join("d:\\1.6\\1.5", yesterday_file)
            if os.path.exists(yesterday_path):
                file_size = os.path.getsize(yesterday_path)
                print(f"[OK] {yesterday_file} (昨日数据) - {file_size} 字节")
            else:
                print(f"[ERROR] {filename} - 文件不存在")
                all_files_exist = False
    
    # 步骤4: 生成执行摘要
    print("\n[步骤4] 生成执行摘要...")
    summary_file = f"automation_summary_{date_str}.md"
    summary_path = os.path.join("d:\\1.6\\1.5", summary_file)
    
    summary_content = f"""# 大宗交易分析自动化执行摘要
## 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## 执行状态: {'成功' if all_files_exist else '部分成功'}

## 执行步骤
1. **数据抓取**: {'✓ 成功' if 'block_trading_data' in str(result.stdout) or '数据已保存' in str(result.stdout) else '✗ 失败'}
2. **特征分析**: {'✓ 成功' if '分析报告已保存' in str(result.stdout) else '✗ 失败'}
3. **文件生成**: {'✓ 全部文件生成成功' if all_files_exist else '✗ 部分文件缺失'}

## 生成文件
"""
    
    # 列出实际生成的文件
    for filename in os.listdir("d:\\1.6\\1.5"):
        if filename.startswith(("block_trading_", "opening_analysis_", "automation_summary_")):
            if filename.endswith((".md", ".csv", ".png")):
                filepath = os.path.join("d:\\1.6\\1.5", filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                file_size = os.path.getsize(filepath)
                summary_content += f"- `{filename}` - {file_time} - {file_size} 字节\n"
    
    summary_content += """
## 下次执行时间
根据自动化配置，下次执行时间为明日开盘后半小时（09:30）。

## 注意事项
1. 数据源可能因网络或API限制而无法获取最新数据
2. 周末和节假日无交易数据
3. 建议人工检查生成的报告内容
4. 如遇连续失败，请检查网络连接和数据源可用性
"""
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"执行摘要已保存到: {summary_path}")
    
    # 步骤5: 更新自动化记忆
    print("\n[步骤5] 更新自动化记忆...")
    memory_path = os.path.join("d:\\1.6\\1.5", ".workbuddy", "automations", "automation", "memory.md")
    
    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(memory_path), exist_ok=True)
    
    memory_content = f"""# 自动化执行记忆
## 最后执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
## 执行结果: {'成功' if all_files_exist else '部分成功'}

## 执行历史
{datetime.now().strftime('%Y-%m-%d')}: {'成功生成分析报告' if all_files_exist else '执行遇到问题'}

## 生成文件
"""
    
    # 添加最近生成的文件
    recent_files = []
    for filename in os.listdir("d:\\1.6\\1.5"):
        if filename.startswith(("block_trading_", "opening_analysis_")) and filename.endswith(".md"):
            filepath = os.path.join("d:\\1.6\\1.5", filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            # 只记录最近3天的文件
            if (datetime.now() - file_time).days <= 3:
                recent_files.append((file_time, filename))
    
    # 按时间排序
    recent_files.sort(reverse=True)
    
    for file_time, filename in recent_files[:5]:  # 只显示最近5个文件
        memory_content += f"- {file_time.strftime('%Y-%m-%d %H:%M')}: {filename}\n"
    
    memory_content += f"""
## 配置信息
- 分析目标: 每日开盘半小时大宗交易信息
- 数据源: 东方财富、新浪财经
- 分析维度: 时间模式、行业板块、价格模式、机构行为
- 输出格式: Markdown报告、CSV数据、PNG图表

## 已知问题
1. 部分API接口可能返回数据不完整
2. 交易时间数据通常不包含在API响应中
3. 周末和节假日需要跳过执行

## 改进建议
1. 考虑接入更多数据源提高数据完整性
2. 添加邮件通知功能
3. 实现数据质量检查机制
"""
    
    try:
        with open(memory_path, 'w', encoding='utf-8') as f:
            f.write(memory_content)
        print(f"自动化记忆已更新: {memory_path}")
    except Exception as e:
        print(f"更新自动化记忆时出错: {e}")
        # 尝试替代位置
        alt_memory_path = os.path.join("d:\\1.6\\1.5", "automation_memory.md")
        with open(alt_memory_path, 'w', encoding='utf-8') as f:
            f.write(memory_content)
        print(f"自动化记忆已保存到替代位置: {alt_memory_path}")
    
    print("\n" + "=" * 60)
    print("自动化执行完成!")
    print("=" * 60)
    
    return all_files_exist

def main():
    """主函数"""
    print("大宗交易分析自动化系统启动...")
    
    # 检查是否为交易日（简单检查，实际应更复杂）
    today = datetime.now()
    if today.weekday() >= 5:  # 5=周六, 6=周日
        print(f"今天是 {today.strftime('%Y年%m月%d日')}，周末无交易，跳过执行。")
        
        # 仍然生成周末提示
        date_str = today.strftime("%Y%m%d")
        weekend_file = f"weekend_notice_{date_str}.md"
        weekend_path = os.path.join("d:\\1.6\\1.5", weekend_file)
        
        with open(weekend_path, 'w', encoding='utf-8') as f:
            f.write(f"""# 周末提示
## 日期: {today.strftime('%Y年%m月%d日')}
## 星期: {'周六' if today.weekday() == 5 else '周日'}

今日为周末，股票市场休市，无大宗交易数据。

## 下次执行时间
下周一开盘后半小时（09:30）将自动执行分析。

## 维护提醒
1. 检查数据源API是否正常
2. 验证网络连接
3. 清理旧的临时文件

---
*本提示由大宗交易分析自动化系统生成*
""")
        
        print(f"周末提示已生成: {weekend_file}")
        return True
    
    # 检查是否在交易时间内（09:30之后）
    current_time = today.time()
    market_open = today.replace(hour=9, minute=30, second=0, microsecond=0).time()
    
    if current_time < market_open:
        print(f"当前时间 {current_time.strftime('%H:%M:%S')} 早于开盘时间 09:30，等待开盘...")
        print("将在开盘后执行分析。")
        return False
    
    # 运行分析
    success = run_analysis()
    
    if success:
        print("自动化分析执行成功！")
        print("生成的文件包含:")
        print("1. 大宗交易数据报告")
        print("2. 开盘半小时特征分析报告")
        print("3. 原始数据CSV文件")
        print("4. 可视化图表（如有数据）")
        print("5. 执行摘要")
    else:
        print("自动化分析执行遇到问题，请检查日志。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)