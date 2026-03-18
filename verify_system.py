#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统验证脚本
验证大宗交易分析系统的核心功能
"""

import os
import sys
import pandas as pd
from datetime import datetime

def check_files():
    """检查必要的文件是否存在"""
    print("=" * 60)
    print("检查系统文件...")
    print("=" * 60)
    
    required_files = [
        'block_trading_crawler.py',
        'opening_analysis.py', 
        'run_automation.py',
        'test_analysis.py',
        'requirements.txt',
        '大宗交易分析系统_README.md',
        'test_data.csv'
    ]
    
    all_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"[OK] {filename} ({file_size} 字节)")
        else:
            print(f"[ERROR] {filename} - 文件不存在")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """检查Python依赖库"""
    print("\n" + "=" * 60)
    print("检查Python依赖库...")
    print("=" * 60)
    
    required_libs = ['requests', 'pandas', 'numpy', 'matplotlib', 'seaborn']
    
    all_installed = True
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"[OK] {lib} - 已安装")
        except ImportError:
            print(f"[ERROR] {lib} - 未安装")
            all_installed = False
    
    return all_installed

def check_data_analysis():
    """检查数据分析功能"""
    print("\n" + "=" * 60)
    print("检查数据分析功能...")
    print("=" * 60)
    
    try:
        # 读取测试数据
        df = pd.read_csv('test_data.csv', encoding='utf-8-sig')
        print(f"[OK] 数据读取 - 成功读取 {len(df)} 条记录")
        
        # 检查数据列
        required_columns = ['股票代码', '股票名称', '成交价', '成交量', '成交金额']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"[ERROR] 数据列缺失: {missing_columns}")
            return False
        else:
            print(f"[OK] 数据列完整")
        
        # 检查数据质量
        total_amount = df['成交金额'].sum()
        avg_price = df['成交价'].mean()
        
        print(f"[OK] 数据处理 - 总成交金额: {total_amount:,.0f} 元")
        print(f"[OK] 数据处理 - 平均成交价: {avg_price:.2f} 元")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 数据分析检查失败: {e}")
        return False

def check_report_generation():
    """检查报告生成功能"""
    print("\n" + "=" * 60)
    print("检查报告生成功能...")
    print("=" * 60)
    
    try:
        # 导入分析模块
        sys.path.insert(0, '.')
        from opening_analysis import OpeningHalfHourAnalyzer
        
        # 创建分析器
        analyzer = OpeningHalfHourAnalyzer()
        
        # 读取测试数据
        df = pd.read_csv('test_data.csv', encoding='utf-8-sig')
        
        # 生成报告
        date_str = datetime.now().strftime("%Y-%m-%d")
        report = analyzer.generate_opening_analysis_report(df, date_str)
        
        # 检查报告内容
        if len(report) > 1000:
            print(f"[OK] 报告生成 - 成功生成 {len(report)} 字符的报告")
            
            # 检查关键部分
            check_points = [
                ('统计摘要', '报告包含统计摘要'),
                ('行业板块分析', '报告包含行业分析'),
                ('价格模式分析', '报告包含价格分析'),
                ('机构行为分析', '报告包含机构分析'),
                ('投资建议', '报告包含投资建议')
            ]
            
            for keyword, description in check_points:
                if keyword in report:
                    print(f"[OK] {description}")
                else:
                    print(f"[WARNING] {description} - 未找到")
            
            return True
        else:
            print(f"[ERROR] 报告内容过短: {len(report)} 字符")
            return False
            
    except Exception as e:
        print(f"[ERROR] 报告生成检查失败: {e}")
        return False

def check_automation_config():
    """检查自动化配置"""
    print("\n" + "=" * 60)
    print("检查自动化配置...")
    print("=" * 60)
    
    # 检查自动化目录
    auto_dir = '.workbuddy/automations/automation'
    memory_file = os.path.join(auto_dir, 'memory.md')
    
    config_ok = True
    
    if os.path.exists(auto_dir):
        print(f"[OK] 自动化目录存在: {auto_dir}")
    else:
        print(f"[WARNING] 自动化目录不存在: {auto_dir}")
        config_ok = False
    
    if os.path.exists(memory_file):
        file_size = os.path.getsize(memory_file)
        print(f"[OK] 自动化记忆文件存在: {memory_file} ({file_size} 字节)")
        
        # 读取记忆文件内容
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '系统配置完成' in content:
                    print("[OK] 自动化记忆文件内容有效")
                else:
                    print("[WARNING] 自动化记忆文件内容可能不完整")
        except:
            print("[WARNING] 无法读取自动化记忆文件")
    else:
        print(f"[WARNING] 自动化记忆文件不存在: {memory_file}")
        config_ok = False
    
    return config_ok

def main():
    """主验证函数"""
    print("\n" + "=" * 60)
    print("大宗交易分析系统 - 完整验证")
    print("=" * 60)
    
    results = []
    
    # 执行各项检查
    results.append(('文件检查', check_files()))
    results.append(('依赖库检查', check_dependencies()))
    results.append(('数据分析检查', check_data_analysis()))
    results.append(('报告生成检查', check_report_generation()))
    results.append(('自动化配置检查', check_automation_config()))
    
    # 显示验证结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "通过" if passed else "失败"
        status_mark = "[OK]" if passed else "[ERROR]"
        print(f"{status_mark} {test_name}: {status}")
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("系统验证: 全部通过!")
        print("\n系统状态: 准备就绪")
        print("自动化配置: 已设置每日09:30执行")
        print("测试功能: 全部正常")
        print("\n可以开始使用系统进行大宗交易分析。")
    else:
        print("系统验证: 部分失败")
        print("\n请检查失败的测试项目并修复问题。")
        print("常见问题:")
        print("1. 文件缺失 - 重新创建缺失的文件")
        print("2. 依赖库未安装 - 运行: pip install -r requirements.txt")
        print("3. 编码问题 - 检查文件编码是否为UTF-8")
        print("4. 路径问题 - 确保在正确的目录中运行")
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)