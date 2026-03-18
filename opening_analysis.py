#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开盘半小时大宗交易特征分析
专门分析每日开盘半小时内大宗交易的特征和模式
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class OpeningHalfHourAnalyzer:
    """开盘半小时特征分析器"""
    
    def __init__(self):
        self.sectors = {
            '金融': ['银行', '保险', '证券', '信托', '金融科技'],
            '科技': ['半导体', '软件', '硬件', '互联网', '人工智能', '5G'],
            '消费': ['食品饮料', '家电', '零售', '旅游', '餐饮'],
            '医药': ['医药', '医疗器械', '生物科技', '医疗服务'],
            '工业': ['机械', '电气设备', '化工', '建材', '建筑'],
            '能源': ['石油', '煤炭', '电力', '新能源'],
            '其他': []
        }
        
    def analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """
        分析时间模式特征
        
        Args:
            df: 交易数据
            
        Returns:
            时间模式分析结果
        """
        if df.empty:
            return {"error": "没有可分析的数据"}
            
        results = {}
        
        # 1. 交易量时间分布（假设数据已按时间排序）
        if '交易时间' in df.columns:
            try:
                df['交易小时'] = pd.to_datetime(df['交易时间']).dt.hour
                df['交易分钟'] = pd.to_datetime(df['交易时间']).dt.minute
                
                # 开盘半小时内每分钟交易分布
                opening_minutes = df[df['交易小时'] == 9]
                if not opening_minutes.empty:
                    minute_dist = opening_minutes.groupby('交易分钟').agg({
                        '成交金额': 'sum',
                        '成交量': 'sum'
                    }).reset_index()
                    
                    results['每分钟交易分布'] = minute_dist.to_dict('records')
            except:
                pass
        
        # 2. 交易强度分析
        total_amount = df['成交金额'].sum()
        avg_amount_per_trade = df['成交金额'].mean()
        median_amount = df['成交金额'].median()
        
        results['交易强度'] = {
            '总成交金额(万元)': round(total_amount / 10000, 2),
            '平均单笔金额(万元)': round(avg_amount_per_trade / 10000, 2),
            '中位数金额(万元)': round(median_amount / 10000, 2),
            '交易笔数': len(df),
            '金额标准差(万元)': round(df['成交金额'].std() / 10000, 2)
        }
        
        # 3. 大额交易分析（超过平均值的2倍）
        large_trades_threshold = avg_amount_per_trade * 2
        large_trades = df[df['成交金额'] > large_trades_threshold]
        
        results['大额交易'] = {
            '大额交易笔数': len(large_trades),
            '大额交易占比': round(len(large_trades) / len(df) * 100, 2) if len(df) > 0 else 0,
            '大额交易总金额(万元)': round(large_trades['成交金额'].sum() / 10000, 2),
            '大额交易平均金额(万元)': round(large_trades['成交金额'].mean() / 10000, 2) if len(large_trades) > 0 else 0
        }
        
        return results
    
    def analyze_sector_patterns(self, df: pd.DataFrame) -> Dict:
        """
        分析行业板块特征
        
        Args:
            df: 交易数据
            
        Returns:
            行业板块分析结果
        """
        if df.empty or '股票名称' not in df.columns:
            return {"error": "缺少股票名称数据"}
            
        results = {}
        
        # 行业分类
        sector_trades = {}
        sector_amounts = {}
        
        for _, row in df.iterrows():
            stock_name = row['股票名称']
            amount = row['成交金额']
            
            # 确定行业
            sector = '其他'
            for sec, keywords in self.sectors.items():
                for keyword in keywords:
                    if keyword in stock_name:
                        sector = sec
                        break
                if sector != '其他':
                    break
            
            # 统计
            if sector not in sector_trades:
                sector_trades[sector] = 0
                sector_amounts[sector] = 0
            
            sector_trades[sector] += 1
            sector_amounts[sector] += amount
        
        # 计算比例
        total_trades = len(df)
        total_amount = df['成交金额'].sum()
        
        sector_results = []
        for sector in sector_trades:
            trade_count = sector_trades[sector]
            trade_amount = sector_amounts[sector]
            
            sector_results.append({
                '行业': sector,
                '交易笔数': trade_count,
                '交易笔数占比': round(trade_count / total_trades * 100, 2) if total_trades > 0 else 0,
                '成交金额(万元)': round(trade_amount / 10000, 2),
                '金额占比': round(trade_amount / total_amount * 100, 2) if total_amount > 0 else 0,
                '平均单笔金额(万元)': round(trade_amount / trade_count / 10000, 2) if trade_count > 0 else 0
            })
        
        # 按成交金额排序
        sector_results.sort(key=lambda x: x['成交金额(万元)'], reverse=True)
        
        results['行业分布'] = sector_results
        
        # 热门行业分析
        if sector_results:
            top_sector = sector_results[0]
            results['热门行业'] = {
                '最活跃行业': top_sector['行业'],
                '行业交易占比': top_sector['交易笔数占比'],
                '行业金额占比': top_sector['金额占比']
            }
        
        return results
    
    def analyze_price_patterns(self, df: pd.DataFrame) -> Dict:
        """
        分析价格模式特征
        
        Args:
            df: 交易数据（需要包含成交价和收盘价）
            
        Returns:
            价格模式分析结果
        """
        if df.empty:
            return {"error": "没有可分析的数据"}
            
        results = {}
        
        # 检查是否有价格数据
        has_price_data = '成交价' in df.columns and '收盘价' in df.columns
        
        if has_price_data:
            # 1. 折溢率分析
            if '折溢率' in df.columns:
                discount_analysis = self._analyze_discount_rate(df)
                results.update(discount_analysis)
            else:
                # 计算折溢率
                df['计算折溢率'] = ((df['成交价'] - df['收盘价']) / df['收盘价'] * 100)
                discount_analysis = self._analyze_discount_rate(df, '计算折溢率')
                results.update(discount_analysis)
            
            # 2. 价格区间分析
            price_ranges = {
                '低价股(<10元)': len(df[df['成交价'] < 10]),
                '中价股(10-50元)': len(df[(df['成交价'] >= 10) & (df['成交价'] < 50)]),
                '高价股(50-100元)': len(df[(df['成交价'] >= 50) & (df['成交价'] < 100)]),
                '高价股(≥100元)': len(df[df['成交价'] >= 100])
            }
            
            results['价格区间分布'] = price_ranges
            
            # 3. 价格与金额关系
            if len(df) > 1:
                # 计算相关性
                correlation = df['成交价'].corr(df['成交金额'])
                results['价格金额相关性'] = round(correlation, 4)
        
        return results
    
    def _analyze_discount_rate(self, df: pd.DataFrame, discount_col: str = '折溢率') -> Dict:
        """分析折溢率特征"""
        results = {}
        
        discount_rates = df[discount_col]
        
        results['折溢率统计'] = {
            '平均折溢率': round(discount_rates.mean(), 2),
            '中位数折溢率': round(discount_rates.median(), 2),
            '最大折溢率': round(discount_rates.max(), 2),
            '最小折溢率': round(discount_rates.min(), 2),
            '标准差': round(discount_rates.std(), 2)
        }
        
        # 折溢率分布
        discount_dist = {
            '大幅折价(<-5%)': len(discount_rates[discount_rates < -5]),
            '小幅折价(-5%~0%)': len(discount_rates[(discount_rates >= -5) & (discount_rates < 0)]),
            '平价(0%)': len(discount_rates[discount_rates == 0]),
            '小幅溢价(0%~5%)': len(discount_rates[(discount_rates > 0) & (discount_rates <= 5)]),
            '大幅溢价(>5%)': len(discount_rates[discount_rates > 5])
        }
        
        results['折溢率分布'] = discount_dist
        
        # 折溢率与金额关系
        if len(df) > 1:
            # 按折溢率分组
            df['折溢率分组'] = pd.cut(df[discount_col], 
                                     bins=[-float('inf'), -5, 0, 0.001, 5, float('inf')],
                                     labels=['大幅折价', '小幅折价', '平价', '小幅溢价', '大幅溢价'])
            
            discount_group_stats = df.groupby('折溢率分组').agg({
                '成交金额': ['sum', 'mean', 'count']
            }).round(2)
            
            results['折溢率分组统计'] = discount_group_stats.to_dict()
        
        return results
    
    def analyze_institutional_behavior(self, df: pd.DataFrame) -> Dict:
        """
        分析机构行为特征
        
        Args:
            df: 交易数据（需要包含营业部信息）
            
        Returns:
            机构行为分析结果
        """
        if df.empty:
            return {"error": "没有可分析的数据"}
            
        results = {}
        
        # 检查是否有营业部数据
        has_buyer_data = '买方营业部' in df.columns
        has_seller_data = '卖方营业部' in df.columns
        
        if has_buyer_data:
            # 买方分析
            buyer_stats = self._analyze_broker_behavior(df, '买方营业部', '买方')
            results.update(buyer_stats)
        
        if has_seller_data:
            # 卖方分析
            seller_stats = self._analyze_broker_behavior(df, '卖方营业部', '卖方')
            results.update(seller_stats)
        
        if has_buyer_data and has_seller_data:
            # 分析买卖方匹配
            match_stats = self._analyze_buyer_seller_match(df)
            results.update(match_stats)
        
        return results
    
    def _analyze_broker_behavior(self, df: pd.DataFrame, broker_col: str, side: str) -> Dict:
        """分析营业部行为"""
        results = {}
        
        # 过滤空值
        broker_data = df[df[broker_col].notna() & (df[broker_col] != '')]
        
        if broker_data.empty:
            results[f'{side}营业部分析'] = {'备注': '无有效营业部数据'}
            return results
        
        # 营业部统计
        broker_counts = broker_data[broker_col].value_counts()
        broker_amounts = broker_data.groupby(broker_col)['成交金额'].sum()
        
        top_brokers = []
        for broker, count in broker_counts.head(10).items():
            amount = broker_amounts.get(broker, 0)
            top_brokers.append({
                '营业部': broker,
                '交易笔数': count,
                '交易笔数占比': round(count / len(broker_data) * 100, 2),
                '成交金额(万元)': round(amount / 10000, 2),
                '平均每笔金额(万元)': round(amount / count / 10000, 2) if count > 0 else 0
            })
        
        results[f'{side}营业部分析'] = {
            '有效数据笔数': len(broker_data),
            '涉及营业部数量': len(broker_counts),
            '前十大营业部': top_brokers,
            '营业部集中度': round(broker_counts.head(5).sum() / len(broker_data) * 100, 2) if len(broker_data) > 0 else 0
        }
        
        return results
    
    def _analyze_buyer_seller_match(self, df: pd.DataFrame) -> Dict:
        """分析买卖方匹配情况"""
        results = {}
        
        # 查找同一营业部既买又卖的情况
        same_broker_trades = df[
            df['买方营业部'].notna() & 
            df['卖方营业部'].notna() & 
            (df['买方营业部'] == df['卖方营业部'])
        ]
        
        results['买卖匹配分析'] = {
            '同一营业部交易笔数': len(same_broker_trades),
            '同一营业部交易占比': round(len(same_broker_trades) / len(df) * 100, 2) if len(df) > 0 else 0,
            '同一营业部成交金额(万元)': round(same_broker_trades['成交金额'].sum() / 10000, 2)
        }
        
        return results
    
    def generate_opening_analysis_report(self, df: pd.DataFrame, date_str: str) -> str:
        """
        生成开盘半小时专门分析报告
        
        Args:
            df: 交易数据
            date_str: 日期
            
        Returns:
            分析报告
        """
        report = f"""# 开盘半小时大宗交易特征分析报告
## 分析日期: {date_str}
## 分析时段: 09:30-10:00
## 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if df.empty:
            report += "## 数据状态\n暂无有效交易数据\n"
            return report
        
        report += f"## 数据概况\n"
        report += f"- 总交易笔数: **{len(df)}** 笔\n"
        report += f"- 总成交金额: **{round(df['成交金额'].sum() / 100000000, 2)}** 亿元\n"
        report += f"- 涉及股票数量: **{df['股票代码'].nunique()}** 只\n"
        
        # 执行各项分析
        print("正在分析时间模式...")
        temporal_results = self.analyze_temporal_patterns(df)
        
        print("正在分析行业板块...")
        sector_results = self.analyze_sector_patterns(df)
        
        print("正在分析价格模式...")
        price_results = self.analyze_price_patterns(df)
        
        print("正在分析机构行为...")
        institutional_results = self.analyze_institutional_behavior(df)
        
        # 1. 时间模式分析
        report += "\n## 一、时间模式分析\n"
        if 'error' not in temporal_results:
            intensity = temporal_results.get('交易强度', {})
            large_trades = temporal_results.get('大额交易', {})
            
            report += f"""
### 交易强度
| 指标 | 数值 |
|------|------|
| 总成交金额 | {intensity.get('总成交金额(万元)', 0)} 万元 |
| 平均单笔金额 | {intensity.get('平均单笔金额(万元)', 0)} 万元 |
| 交易笔数 | {intensity.get('交易笔数', 0)} 笔 |
| 金额标准差 | {intensity.get('金额标准差(万元)', 0)} 万元 |

### 大额交易分析
| 指标 | 数值 |
|------|------|
| 大额交易笔数 | {large_trades.get('大额交易笔数', 0)} 笔 |
| 大额交易占比 | {large_trades.get('大额交易占比', 0)}% |
| 大额交易总金额 | {large_trades.get('大额交易总金额(万元)', 0)} 万元 |
| 大额交易平均金额 | {large_trades.get('大额交易平均金额(万元)', 0)} 万元 |
"""
        
        # 2. 行业板块分析
        report += "\n## 二、行业板块分析\n"
        if 'error' not in sector_results and '行业分布' in sector_results:
            sector_data = sector_results['行业分布']
            
            report += "### 行业交易分布（按成交金额排名）\n"
            report += "| 行业 | 交易笔数 | 笔数占比 | 成交金额(万元) | 金额占比 | 平均单笔金额(万元) |\n"
            report += "|------|----------|----------|----------------|----------|--------------------|\n"
            
            for sector in sector_data[:10]:  # 显示前10个行业
                report += f"| {sector['行业']} | {sector['交易笔数']} | {sector['交易笔数占比']}% | {sector['成交金额(万元)']} | {sector['金额占比']}% | {sector['平均单笔金额(万元)']} |\n"
            
            if '热门行业' in sector_results:
                hot_sector = sector_results['热门行业']
                report += f"\n### 热门行业\n"
                report += f"- **最活跃行业**: {hot_sector['最活跃行业']}\n"
                report += f"- 该行业交易笔数占比: {hot_sector['行业交易占比']}%\n"
                report += f"- 该行业成交金额占比: {hot_sector['行业金额占比']}%\n"
        
        # 3. 价格模式分析
        report += "\n## 三、价格模式分析\n"
        if 'error' not in price_results:
            # 折溢率分析
            if '折溢率统计' in price_results:
                discount_stats = price_results['折溢率统计']
                report += "### 折溢率统计\n"
                report += "| 指标 | 数值 |\n|------|------|\n"
                report += f"| 平均折溢率 | {discount_stats['平均折溢率']}% |\n"
                report += f"| 中位数折溢率 | {discount_stats['中位数折溢率']}% |\n"
                report += f"| 最大折溢率 | {discount_stats['最大折溢率']}% |\n"
                report += f"| 最小折溢率 | {discount_stats['最小折溢率']}% |\n"
                report += f"| 标准差 | {discount_stats['标准差']} |\n"
            
            # 折溢率分布
            if '折溢率分布' in price_results:
                discount_dist = price_results['折溢率分布']
                report += "\n### 折溢率分布\n"
                report += "| 折溢率区间 | 交易笔数 |\n|------------|----------|\n"
                report += f"| 大幅折价(<-5%) | {discount_dist['大幅折价(<-5%)']} |\n"
                report += f"| 小幅折价(-5%~0%) | {discount_dist['小幅折价(-5%~0%)']} |\n"
                report += f"| 平价(0%) | {discount_dist['平价(0%)']} |\n"
                report += f"| 小幅溢价(0%~5%) | {discount_dist['小幅溢价(0%~5%)']} |\n"
                report += f"| 大幅溢价(>5%) | {discount_dist['大幅溢价(>5%)']} |\n"
                
                # 解读
                total_discount = discount_dist['大幅折价(<-5%)'] + discount_dist['小幅折价(-5%~0%)']
                total_premium = discount_dist['小幅溢价(0%~5%)'] + discount_dist['大幅溢价(>5%)']
                
                if total_discount > total_premium:
                    report += "\n**市场解读**: 折价交易占主导，显示卖方急于出货，可能反映市场悲观情绪。\n"
                else:
                    report += "\n**市场解读**: 溢价交易较多，显示买方愿意高价买入，可能反映市场乐观情绪。\n"
            
            # 价格区间
            if '价格区间分布' in price_results:
                price_ranges = price_results['价格区间分布']
                report += "\n### 股价区间分布\n"
                report += "| 股价区间 | 交易笔数 |\n|----------|----------|\n"
                for range_name, count in price_ranges.items():
                    report += f"| {range_name} | {count} |\n"
        
        # 4. 机构行为分析
        report += "\n## 四、机构行为分析\n"
        if 'error' not in institutional_results:
            # 买方分析
            if '买方营业部分析' in institutional_results:
                buyer_analysis = institutional_results['买方营业部分析']
                if '前十大营业部' in buyer_analysis:
                    report += "### 活跃买方营业部（按交易笔数）\n"
                    report += "| 排名 | 营业部 | 交易笔数 | 笔数占比 | 成交金额(万元) | 平均每笔金额(万元) |\n"
                    report += "|------|--------|----------|----------|----------------|--------------------|\n"
                    
                    for i, broker in enumerate(buyer_analysis['前十大营业部'][:10], 1):
                        report += f"| {i} | {broker['营业部']} | {broker['交易笔数']} | {broker['交易笔数占比']}% | {broker['成交金额(万元)']} | {broker['平均每笔金额(万元)']} |\n"
                    
                    report += f"\n**买方集中度**: 前五大营业部交易笔数占比 {buyer_analysis.get('营业部集中度', 0)}%\n"
            
            # 卖方分析
            if '卖方营业部分析' in institutional_results:
                seller_analysis = institutional_results['卖方营业部分析']
                if '前十大营业部' in seller_analysis:
                    report += "\n### 活跃卖方营业部（按交易笔数）\n"
                    report += "| 排名 | 营业部 | 交易笔数 | 笔数占比 | 成交金额(万元) | 平均每笔金额(万元) |\n"
                    report += "|------|--------|----------|----------|----------------|--------------------|\n"
                    
                    for i, broker in enumerate(seller_analysis['前十大营业部'][:10], 1):
                        report += f"| {i} | {broker['营业部']} | {broker['交易笔数']} | {broker['交易笔数占比']}% | {broker['成交金额(万元)']} | {broker['平均每笔金额(万元)']} |\n"
            
            # 买卖匹配
            if '买卖匹配分析' in institutional_results:
                match_analysis = institutional_results['买卖匹配分析']
                report += "\n### 买卖方匹配分析\n"
                report += f"- 同一营业部交易笔数: {match_analysis['同一营业部交易笔数']}\n"
                report += f"- 同一营业部交易占比: {match_analysis['同一营业部交易占比']}%\n"
                report += f"- 同一营业部成交金额: {match_analysis['同一营业部成交金额(万元)']} 万元\n"
                
                if match_analysis['同一营业部交易占比'] > 10:
                    report += "**注意**: 同一营业部既买又卖的比例较高，可能存在对倒交易嫌疑。\n"
        
        # 5. 投资建议
        report += "\n## 五、投资建议与风险提示\n"
        report += "### 重点关注\n"
        
        # 基于分析的动态建议
        recommendations = []
        
        # 基于行业分析
        if 'error' not in sector_results and '行业分布' in sector_results:
            top_sectors = sector_results['行业分布'][:3]
            if top_sectors:
                sector_names = [s['行业'] for s in top_sectors]
                recommendations.append(f"1. **关注活跃行业**: {', '.join(sector_names)} 板块大宗交易活跃")
        
        # 基于价格分析
        if 'error' not in price_results and '折溢率分布' in price_results:
            discount_dist = price_results['折溢率分布']
            discount_ratio = (discount_dist['大幅折价(<-5%)'] + discount_dist['小幅折价(-5%~0%)']) / len(df) * 100
            
            if discount_ratio > 60:
                recommendations.append("2. **谨慎对待折价股**: 折价交易比例较高，可能预示短期调整压力")
            elif discount_ratio < 30:
                recommendations.append("2. **关注溢价交易**: 溢价交易占比较高，显示机构买入意愿较强")
        
        # 基于机构行为
        if 'error' not in institutional_results and '买方营业部分析' in institutional_results:
            buyer_analysis = institutional_results['买方营业部分析']
            if buyer_analysis.get('营业部集中度', 0) > 50:
                recommendations.append("3. **注意机构集中度**: 买方机构集中度较高，需关注后续动向")
        
        if recommendations:
            for rec in recommendations:
                report += f"{rec}\n"
        else:
            report += "1. 关注大宗交易活跃的蓝筹股\n"
            report += "2. 注意折价交易带来的短期压力\n"
            report += "3. 跟踪机构营业部的交易动向\n"
        
        report += "\n### 风险提示\n"
        report += """1. **数据局限性**: 开盘半小时数据可能不完整，建议结合全天数据
2. **时间敏感**: 大宗交易对股价影响具有时效性，需及时跟踪
3. **机构意图**: 机构大宗交易可能有多重意图，需结合基本面分析
4. **市场环境**: 需结合当前市场整体环境和政策背景
5. **个人风险承受**: 投资者应根据自身风险承受能力决策\n"""
        
        return report
    
    def create_visualizations(self, df: pd.DataFrame, output_dir: str = "d:\\1.6\\1.5"):
        """
        创建可视化图表
        
        Args:
            df: 交易数据
            output_dir: 输出目录
        """
        if df.empty:
            print("没有数据可创建可视化")
            return
            
        try:
            # 设置图形风格
            sns.set_style("whitegrid")
            plt.figure(figsize=(15, 10))
            
            # 1. 成交金额分布直方图
            plt.subplot(2, 2, 1)
            amount_millions = df['成交金额'] / 10000  # 转换为万元
            plt.hist(amount_millions, bins=20, edgecolor='black', alpha=0.7)
            plt.title('成交金额分布（万元）', fontsize=14)
            plt.xlabel('成交金额（万元）')
            plt.ylabel('频数')
            
            # 2. 行业分布饼图
            plt.subplot(2, 2, 2)
            # 简化的行业分类
            sector_data = self.analyze_sector_patterns(df)
            if 'error' not in sector_data and '行业分布' in sector_data:
                sector_df = pd.DataFrame(sector_data['行业分布'])
                if not sector_df.empty:
                    # 只显示前5大行业，其他合并
                    if len(sector_df) > 5:
                        top_sectors = sector_df.head(5)
                        other_amount = sector_df.iloc[5:]['成交金额(万元)'].sum()
                        other_row = pd.DataFrame([{
                            '行业': '其他',
                            '成交金额(万元)': other_amount
                        }])
                        plot_df = pd.concat([top_sectors, other_row])
                    else:
                        plot_df = sector_df
                    
                    plt.pie(plot_df['成交金额(万元)'], labels=plot_df['行业'], autopct='%1.1f%%')
                    plt.title('行业成交金额分布', fontsize=14)
            
            # 3. 折溢率分布箱线图
            plt.subplot(2, 2, 3)
            if '折溢率' in df.columns:
                plt.boxplot(df['折溢率'].dropna())
                plt.title('折溢率分布箱线图', fontsize=14)
                plt.ylabel('折溢率(%)')
            else:
                plt.text(0.5, 0.5, '无折溢率数据', ha='center', va='center', fontsize=12)
                plt.title('折溢率分布箱线图', fontsize=14)
            
            # 4. 价格与金额散点图
            plt.subplot(2, 2, 4)
            if '成交价' in df.columns:
                plt.scatter(df['成交价'], amount_millions, alpha=0.6)
                plt.title('成交价 vs 成交金额', fontsize=14)
                plt.xlabel('成交价（元）')
                plt.ylabel('成交金额（万元）')
            else:
                plt.text(0.5, 0.5, '无成交价数据', ha='center', va='center', fontsize=12)
                plt.title('成交价 vs 成交金额', fontsize=14)
            
            plt.tight_layout()
            
            # 保存图表
            date_str = datetime.now().strftime("%Y%m%d")
            chart_path = f"{output_dir}\\opening_analysis_chart_{date_str}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"可视化图表已保存到: {chart_path}")
            
        except Exception as e:
            print(f"创建可视化图表时出错: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("开盘半小时大宗交易特征分析工具")
    print("=" * 60)
    
    # 创建分析器
    analyzer = OpeningHalfHourAnalyzer()
    
    # 尝试读取现有数据
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        data_file = f"d:\\1.6\\1.5\\block_trading_data_{date_str}.csv"
        
        print(f"正在读取数据文件: {data_file}")
        df = pd.read_csv(data_file, encoding='utf-8-sig')
        
        if df.empty:
            # 尝试读取昨天的数据
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            data_file = f"d:\\1.6\\1.5\\block_trading_data_{yesterday}.csv"
            print(f"今日数据为空，尝试读取昨日数据: {data_file}")
            df = pd.read_csv(data_file, encoding='utf-8-sig')
            date_str = yesterday
        
        if df.empty:
            print("没有找到有效的交易数据文件")
            return
        
        print(f"成功读取 {len(df)} 条交易数据")
        
        # 生成专门分析报告
        print("\n正在生成开盘半小时特征分析报告...")
        report = analyzer.generate_opening_analysis_report(df, date_str[:4] + '-' + date_str[4:6] + '-' + date_str[6:])
        
        # 保存报告
        report_filename = f"opening_analysis_report_{date_str}.md"
        report_path = f"d:\\1.6\\1.5\\{report_filename}"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"分析报告已保存到: {report_path}")
        
        # 创建可视化图表
        print("正在创建可视化图表...")
        analyzer.create_visualizations(df)
        
        # 显示关键发现
        print("\n" + "=" * 60)
        print("关键发现摘要:")
        print("=" * 60)
        
        # 执行分析获取关键指标
        sector_results = analyzer.analyze_sector_patterns(df)
        price_results = analyzer.analyze_price_patterns(df)
        temporal_results = analyzer.analyze_temporal_patterns(df)
        
        if 'error' not in sector_results and '行业分布' in sector_results:
            top_sector = sector_results['行业分布'][0] if sector_results['行业分布'] else {}
            print(f"最活跃行业: {top_sector.get('行业', '未知')} (交易笔数占比: {top_sector.get('交易笔数占比', 0)}%)")
        
        if 'error' not in price_results and '折溢率统计' in price_results:
            discount_stats = price_results['折溢率统计']
            print(f"平均折溢率: {discount_stats.get('平均折溢率', 0)}%")
        
        if 'error' not in temporal_results and '交易强度' in temporal_results:
            intensity = temporal_results['交易强度']
            print(f"总成交金额: {intensity.get('总成交金额(万元)', 0)} 万元")
            print(f"平均单笔金额: {intensity.get('平均单笔金额(万元)', 0)} 万元")
        
        print(f"\n详细分析请查看报告文件: {report_filename}")
        
    except FileNotFoundError:
        print("未找到数据文件，请先运行 block_trading_crawler.py 获取数据")
    except Exception as e:
        print(f"分析过程中出错: {e}")

if __name__ == "__main__":
    main()