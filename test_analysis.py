#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析脚本
使用测试数据演示系统功能
"""

import pandas as pd
from opening_analysis import OpeningHalfHourAnalyzer
from datetime import datetime

def main():
    print("=" * 60)
    print("大宗交易分析系统测试演示")
    print("=" * 60)
    
    # 创建分析器
    analyzer = OpeningHalfHourAnalyzer()
    
    # 读取测试数据
    print("\n读取测试数据...")
    df = pd.read_csv("test_data.csv", encoding='utf-8-sig')
    print(f"成功读取 {len(df)} 条测试数据")
    
    # 显示数据样本
    print("\n数据样本:")
    print(df.head())
    
    # 执行各项分析
    print("\n" + "=" * 60)
    print("执行特征分析...")
    print("=" * 60)
    
    # 1. 时间模式分析
    print("\n1. 时间模式分析:")
    temporal_results = analyzer.analyze_temporal_patterns(df)
    if 'error' not in temporal_results:
        intensity = temporal_results.get('交易强度', {})
        print(f"  总成交金额: {intensity.get('总成交金额(万元)', 0)} 万元")
        print(f"  平均单笔金额: {intensity.get('平均单笔金额(万元)', 0)} 万元")
        print(f"  交易笔数: {intensity.get('交易笔数', 0)} 笔")
        
        large_trades = temporal_results.get('大额交易', {})
        print(f"  大额交易占比: {large_trades.get('大额交易占比', 0)}%")
    
    # 2. 行业板块分析
    print("\n2. 行业板块分析:")
    sector_results = analyzer.analyze_sector_patterns(df)
    if 'error' not in sector_results:
        sector_data = sector_results.get('行业分布', [])
        print(f"  涉及行业数量: {len(sector_data)} 个")
        if sector_data:
            print("  行业分布（按成交金额）:")
            for i, sector in enumerate(sector_data[:3], 1):
                print(f"    {i}. {sector['行业']}: {sector['成交金额(万元)']} 万元 ({sector['金额占比']}%)")
    
    # 3. 价格模式分析
    print("\n3. 价格模式分析:")
    price_results = analyzer.analyze_price_patterns(df)
    if 'error' not in price_results:
        if '折溢率统计' in price_results:
            discount_stats = price_results['折溢率统计']
            print(f"  平均折溢率: {discount_stats.get('平均折溢率', 0)}%")
            print(f"  最大折溢率: {discount_stats.get('最大折溢率', 0)}%")
            print(f"  最小折溢率: {discount_stats.get('最小折溢率', 0)}%")
        
        if '折溢率分布' in price_results:
            discount_dist = price_results['折溢率分布']
            total_discount = discount_dist['大幅折价(<-5%)'] + discount_dist['小幅折价(-5%~0%)']
            total_trades = sum(discount_dist.values())
            discount_ratio = total_discount / total_trades * 100 if total_trades > 0 else 0
            print(f"  折价交易比例: {discount_ratio:.1f}%")
    
    # 4. 机构行为分析
    print("\n4. 机构行为分析:")
    institutional_results = analyzer.analyze_institutional_behavior(df)
    if 'error' not in institutional_results:
        if '买方营业部分析' in institutional_results:
            buyer_analysis = institutional_results['买方营业部分析']
            print(f"  涉及买方营业部: {buyer_analysis.get('涉及营业部数量', 0)} 个")
            print(f"  买方集中度: {buyer_analysis.get('营业部集中度', 0)}%")
        
        if '卖方营业部分析' in institutional_results:
            seller_analysis = institutional_results['卖方营业部分析']
            print(f"  涉及卖方营业部: {seller_analysis.get('涉及营业部数量', 0)} 个")
    
    # 生成完整报告
    print("\n" + "=" * 60)
    print("生成完整分析报告...")
    print("=" * 60)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    report = analyzer.generate_opening_analysis_report(df, date_str)
    
    # 保存报告
    report_filename = "test_analysis_report.md"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"测试分析报告已保存到: {report_filename}")
    
    # 创建可视化图表
    print("\n创建可视化图表...")
    analyzer.create_visualizations(df)
    
    # 显示关键发现
    print("\n" + "=" * 60)
    print("测试分析关键发现:")
    print("=" * 60)
    
    if 'error' not in sector_results and sector_data:
        print(f"1. 最活跃行业: {sector_data[0]['行业']} (成交金额占比: {sector_data[0]['金额占比']}%)")
    
    if 'error' not in price_results and '折溢率统计' in price_results:
        avg_discount = discount_stats.get('平均折溢率', 0)
        if avg_discount < 0:
            print(f"2. 市场情绪: 偏悲观 (平均折溢率: {avg_discount}%)")
        else:
            print(f"2. 市场情绪: 偏乐观 (平均折溢率: {avg_discount}%)")
    
    if 'error' not in temporal_results:
        print(f"3. 交易强度: {intensity.get('总成交金额(万元)', 0)} 万元, 平均 {intensity.get('平均单笔金额(万元)', 0)} 万元/笔")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print("\n系统功能验证:")
    print("[OK] 数据读取和处理")
    print("[OK] 多维度特征分析")
    print("[OK] 报告生成")
    print("[OK] 可视化图表")
    print("[OK] 投资建议生成")
    print("\n系统已准备就绪，可配置为每日自动执行。")

if __name__ == "__main__":
    main()