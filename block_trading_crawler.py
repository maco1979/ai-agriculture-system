#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大宗交易数据抓取分析脚本
用于抓取每日开盘半小时的大宗交易信息并进行分析
"""

import requests
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class BlockTradingAnalyzer:
    """大宗交易数据分析器"""
    
    def __init__(self):
        self.base_url = "http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://data.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
    def get_block_trading_data(self, date_str: str = None) -> pd.DataFrame:
        """
        获取指定日期的大宗交易数据
        
        Args:
            date_str: 日期字符串，格式：YYYY-MM-DD，默认为当天
            
        Returns:
            DataFrame包含大宗交易数据
        """
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        # 尝试从不同接口获取数据
        data_frames = []
        
        # 方法1：从东方财富API获取
        try:
            df1 = self._get_from_eastmoney_api(date_str)
            if df1 is not None and not df1.empty:
                data_frames.append(df1)
                print(f"从东方财富API获取到 {len(df1)} 条大宗交易数据")
        except Exception as e:
            print(f"东方财富API获取失败: {e}")
            
        # 方法2：从新浪财经获取
        try:
            df2 = self._get_from_sina_api(date_str)
            if df2 is not None and not df2.empty:
                data_frames.append(df2)
                print(f"从新浪财经获取到 {len(df2)} 条大宗交易数据")
        except Exception as e:
            print(f"新浪财经API获取失败: {e}")
            
        # 合并数据
        if data_frames:
            combined_df = pd.concat(data_frames, ignore_index=True)
            # 去重处理
            combined_df = combined_df.drop_duplicates(subset=['股票代码', '交易时间', '成交金额'], keep='first')
            return combined_df
        else:
            return pd.DataFrame()
            
    def _get_from_eastmoney_api(self, date_str: str) -> pd.DataFrame:
        """从东方财富API获取数据"""
        # 构建请求参数
        params = {
            'type': 'NS',
            'sty': 'NSST',
            'st': '5',
            'sr': '-1',
            'p': '1',
            'ps': '500',  # 每页显示数量
            'js': 'var data={pages:(pc),data:[(x)]}',
            'mkt': '0',  # 0=全部，1=沪市，2=深市
            'stat': '0',
            'cmdC': '',
            'date': date_str.replace('-', ''),
            'rt': str(int(time.time() * 1000))
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                content = response.text
                # 解析JSON数据
                match = re.search(r'var data=\{pages:(\d+),data:\[(.*?)\]\}', content)
                if match:
                    data_str = match.group(2)
                    if data_str:
                        # 解析数据
                        data_list = []
                        items = data_str.split('","')
                        for item in items:
                            fields = item.split(',')
                            if len(fields) >= 10:
                                try:
                                    data_dict = {
                                        '股票代码': fields[1] if len(fields) > 1 else '',
                                        '股票名称': fields[2] if len(fields) > 2 else '',
                                        '成交价': float(fields[3]) if len(fields) > 3 and fields[3] else 0,
                                        '收盘价': float(fields[4]) if len(fields) > 4 and fields[4] else 0,
                                        '折溢率': float(fields[5].replace('%', '')) if len(fields) > 5 and fields[5] else 0,
                                        '成交量': float(fields[6]) if len(fields) > 6 and fields[6] else 0,
                                        '成交金额': float(fields[7]) if len(fields) > 7 and fields[7] else 0,
                                        '买方营业部': fields[8] if len(fields) > 8 else '',
                                        '卖方营业部': fields[9] if len(fields) > 9 else '',
                                        '交易日期': date_str
                                    }
                                    data_list.append(data_dict)
                                except ValueError:
                                    continue
                        
                        if data_list:
                            df = pd.DataFrame(data_list)
                            df['数据来源'] = '东方财富'
                            return df
        except Exception as e:
            print(f"东方财富API请求异常: {e}")
            
        return pd.DataFrame()
    
    def _get_from_sina_api(self, date_str: str) -> pd.DataFrame:
        """从新浪财经获取大宗交易数据"""
        sina_url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
        
        params = {
            'page': '1',
            'num': '100',
            'sort': 'amount',
            'asc': '0',
            'node': 'blocktrade',
            '_s_r_a': 'page'
        }
        
        try:
            response = requests.get(sina_url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                # 新浪返回的是JSONP格式，需要解析
                content = response.text
                # 尝试解析JSON
                if content.startswith('['):
                    data = json.loads(content)
                    if data and isinstance(data, list):
                        data_list = []
                        for item in data:
                            if isinstance(item, dict):
                                data_dict = {
                                    '股票代码': item.get('symbol', ''),
                                    '股票名称': item.get('name', ''),
                                    '成交价': float(item.get('price', 0)),
                                    '成交量': float(item.get('volume', 0)),
                                    '成交金额': float(item.get('amount', 0)),
                                    '买方营业部': item.get('buyer', ''),
                                    '卖方营业部': item.get('seller', ''),
                                    '交易日期': date_str
                                }
                                data_list.append(data_dict)
                        
                        if data_list:
                            df = pd.DataFrame(data_list)
                            df['数据来源'] = '新浪财经'
                            return df
        except Exception as e:
            print(f"新浪财经API请求异常: {e}")
            
        return pd.DataFrame()
    
    def filter_opening_half_hour(self, df: pd.DataFrame, market_open_time: str = "09:30:00") -> pd.DataFrame:
        """
        筛选开盘半小时内的交易数据
        
        Args:
            df: 原始数据
            market_open_time: 市场开盘时间
            
        Returns:
            开盘半小时内的数据
        """
        if df.empty:
            return df
            
        # 这里需要实际的时间数据，但API通常不提供具体交易时间
        # 在实际应用中，需要更精确的时间数据源
        print("注意：当前API未提供具体交易时间，假设所有数据为开盘半小时内")
        return df
    
    def analyze_block_trading(self, df: pd.DataFrame) -> Dict:
        """
        分析大宗交易数据
        
        Args:
            df: 大宗交易数据
            
        Returns:
            分析结果字典
        """
        if df.empty:
            return {"error": "没有可分析的数据"}
            
        analysis_result = {
            "统计摘要": {},
            "热门股票": [],
            "机构行为": {},
            "市场情绪": {}
        }
        
        # 基本统计
        total_trades = len(df)
        total_amount = df['成交金额'].sum() / 100000000  # 转换为亿元
        avg_amount = df['成交金额'].mean() / 10000  # 转换为万元
        max_amount = df['成交金额'].max() / 10000  # 转换为万元
        min_amount = df['成交金额'].min() / 10000  # 转换为万元
        
        analysis_result["统计摘要"] = {
            "总交易笔数": total_trades,
            "总成交金额(亿元)": round(total_amount, 2),
            "平均每笔金额(万元)": round(avg_amount, 2),
            "最大单笔金额(万元)": round(max_amount, 2),
            "最小单笔金额(万元)": round(min_amount, 2)
        }
        
        # 热门股票分析（按成交金额排序）
        if not df.empty:
            top_stocks = df.groupby(['股票代码', '股票名称']).agg({
                '成交金额': 'sum',
                '成交量': 'sum',
                '成交价': 'mean'
            }).reset_index()
            
            top_stocks = top_stocks.sort_values('成交金额', ascending=False).head(10)
            
            for _, row in top_stocks.iterrows():
                analysis_result["热门股票"].append({
                    "股票代码": row['股票代码'],
                    "股票名称": row['股票名称'],
                    "总成交金额(万元)": round(row['成交金额'] / 10000, 2),
                    "总成交量(万股)": round(row['成交量'] / 10000, 2),
                    "平均成交价": round(row['成交价'], 2)
                })
        
        # 机构行为分析（通过营业部信息）
        buyer_counts = df['买方营业部'].value_counts().head(5)
        seller_counts = df['卖方营业部'].value_counts().head(5)
        
        analysis_result["机构行为"]["活跃买方营业部"] = buyer_counts.to_dict()
        analysis_result["机构行为"]["活跃卖方营业部"] = seller_counts.to_dict()
        
        # 市场情绪分析（通过折溢率）
        if '折溢率' in df.columns:
            discount_count = len(df[df['折溢率'] < 0])
            premium_count = len(df[df['折溢率'] > 0])
            par_count = len(df[df['折溢率'] == 0])
            
            analysis_result["市场情绪"]["折价交易笔数"] = discount_count
            analysis_result["市场情绪"]["溢价交易笔数"] = premium_count
            analysis_result["市场情绪"]["平价交易笔数"] = par_count
            analysis_result["市场情绪"]["折价交易比例"] = round(discount_count / total_trades * 100, 2) if total_trades > 0 else 0
            analysis_result["市场情绪"]["溢价交易比例"] = round(premium_count / total_trades * 100, 2) if total_trades > 0 else 0
        else:
            analysis_result["市场情绪"]["备注"] = "折溢率数据缺失"
        
        return analysis_result
    
    def generate_report(self, analysis_result: Dict, date_str: str) -> str:
        """
        生成分析报告
        
        Args:
            analysis_result: 分析结果
            date_str: 日期
            
        Returns:
            报告字符串
        """
        report = f"""# 大宗交易开盘半小时分析报告
## 分析日期: {date_str}
## 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        if "error" in analysis_result:
            report += f"### 数据获取异常\n{analysis_result['error']}\n"
            return report
        
        # 统计摘要
        report += "## 一、统计摘要\n"
        stats = analysis_result.get("统计摘要", {})
        if stats:
            report += f"""
| 指标 | 数值 |
|------|------|
| 总交易笔数 | {stats.get('总交易笔数', 0)} 笔 |
| 总成交金额 | {stats.get('总成交金额(亿元)', 0)} 亿元 |
| 平均每笔金额 | {stats.get('平均每笔金额(万元)', 0)} 万元 |
| 最大单笔金额 | {stats.get('最大单笔金额(万元)', 0)} 万元 |
| 最小单笔金额 | {stats.get('最小单笔金额(万元)', 0)} 万元 |

"""
        
        # 热门股票
        report += "## 二、热门股票分析（按成交金额排名）\n"
        top_stocks = analysis_result.get("热门股票", [])
        if top_stocks:
            report += "| 排名 | 股票代码 | 股票名称 | 总成交金额(万元) | 总成交量(万股) | 平均成交价 |\n"
            report += "|------|----------|----------|------------------|----------------|------------|\n"
            for i, stock in enumerate(top_stocks[:10], 1):
                report += f"| {i} | {stock['股票代码']} | {stock['股票名称']} | {stock['总成交金额(万元)']} | {stock['总成交量(万股)']} | {stock['平均成交价']} |\n"
            report += "\n"
        else:
            report += "暂无热门股票数据\n\n"
        
        # 机构行为
        report += "## 三、机构行为分析\n"
        institution = analysis_result.get("机构行为", {})
        if institution:
            report += "### 活跃买方营业部（按交易笔数）\n"
            buyers = institution.get("活跃买方营业部", {})
            if buyers:
                report += "| 营业部 | 交易笔数 |\n|--------|----------|\n"
                for buyer, count in buyers.items():
                    if buyer:  # 过滤空值
                        report += f"| {buyer} | {count} |\n"
                report += "\n"
            
            report += "### 活跃卖方营业部（按交易笔数）\n"
            sellers = institution.get("活跃卖方营业部", {})
            if sellers:
                report += "| 营业部 | 交易笔数 |\n|--------|----------|\n"
                for seller, count in sellers.items():
                    if seller:  # 过滤空值
                        report += f"| {seller} | {count} |\n"
                report += "\n"
        else:
            report += "暂无机构行为数据\n\n"
        
        # 市场情绪
        report += "## 四、市场情绪分析\n"
        sentiment = analysis_result.get("市场情绪", {})
        if "备注" in sentiment:
            report += f"{sentiment['备注']}\n\n"
        else:
            report += f"""
| 情绪指标 | 数值 | 比例 |
|----------|------|------|
| 折价交易笔数 | {sentiment.get('折价交易笔数', 0)} | {sentiment.get('折价交易比例', 0)}% |
| 溢价交易笔数 | {sentiment.get('溢价交易笔数', 0)} | {sentiment.get('溢价交易比例', 0)}% |
| 平价交易笔数 | {sentiment.get('平价交易笔数', 0)} | - |

"""
            
            # 情绪解读
            discount_ratio = sentiment.get('折价交易比例', 0)
            if discount_ratio > 70:
                emotion = "极度悲观"
            elif discount_ratio > 50:
                emotion = "较为悲观"
            elif discount_ratio > 30:
                emotion = "中性偏悲观"
            elif discount_ratio > 10:
                emotion = "中性偏乐观"
            else:
                emotion = "较为乐观"
                
            report += f"### 情绪解读\n当前市场情绪: **{emotion}**\n"
            report += f"折价交易比例 {discount_ratio}%，表明大宗交易卖家更倾向于折价出货。\n\n"
        
        # 投资建议
        report += "## 五、投资建议\n"
        if top_stocks:
            report += "### 重点关注股票\n"
            report += "基于大宗交易活跃度，建议关注以下股票：\n\n"
            for i, stock in enumerate(top_stocks[:5], 1):
                report += f"{i}. **{stock['股票名称']} ({stock['股票代码']})** - 成交金额 {stock['总成交金额(万元)']} 万元\n"
            report += "\n"
        
        report += "### 风险提示\n"
        report += """1. 大宗交易数据仅供参考，不构成投资建议
2. 开盘半小时数据可能不完整，建议结合全天数据综合分析
3. 注意机构减持带来的股价压力
4. 关注大宗交易后的股价走势\n"""
        
        return report
    
    def save_to_csv(self, df: pd.DataFrame, filename: str = None):
        """保存数据到CSV文件"""
        if df.empty:
            print("没有数据可保存")
            return
            
        if filename is None:
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"block_trading_{date_str}.csv"
            
        filepath = f"d:\\1.6\\1.5\\{filename}"
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {filepath}")

def main():
    """主函数"""
    print("=" * 60)
    print("大宗交易开盘半小时分析工具")
    print("=" * 60)
    
    # 创建分析器
    analyzer = BlockTradingAnalyzer()
    
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n分析日期: {today}")
    
    # 获取大宗交易数据
    print("\n正在获取大宗交易数据...")
    df = analyzer.get_block_trading_data(today)
    
    if df.empty:
        # 如果今天没有数据，尝试获取昨天的数据
        print("今日数据为空，尝试获取昨日数据...")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        df = analyzer.get_block_trading_data(yesterday)
        today = yesterday
    
    if df.empty:
        print("无法获取大宗交易数据，请检查网络连接或数据源")
        return
    
    print(f"成功获取 {len(df)} 条大宗交易数据")
    
    # 筛选开盘半小时数据（实际应用中需要时间数据）
    opening_df = analyzer.filter_opening_half_hour(df)
    print(f"开盘半小时数据: {len(opening_df)} 条")
    
    # 分析数据
    print("\n正在分析数据...")
    analysis_result = analyzer.analyze_block_trading(opening_df)
    
    # 生成报告
    print("正在生成分析报告...")
    report = analyzer.generate_report(analysis_result, today)
    
    # 保存报告
    report_filename = f"block_trading_report_{today.replace('-', '')}.md"
    report_path = f"d:\\1.6\\1.5\\{report_filename}"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n分析报告已保存到: {report_path}")
    
    # 保存原始数据
    data_filename = f"block_trading_data_{today.replace('-', '')}.csv"
    analyzer.save_to_csv(df, data_filename)
    
    # 显示报告摘要
    print("\n" + "=" * 60)
    print("报告摘要:")
    print("=" * 60)
    
    if "统计摘要" in analysis_result:
        stats = analysis_result["统计摘要"]
        print(f"总交易笔数: {stats.get('总交易笔数', 0)} 笔")
        print(f"总成交金额: {stats.get('总成交金额(亿元)', 0)} 亿元")
        print(f"平均每笔金额: {stats.get('平均每笔金额(万元)', 0)} 万元")
    
    if "市场情绪" in analysis_result and "折价交易比例" in analysis_result["市场情绪"]:
        discount_ratio = analysis_result["市场情绪"]["折价交易比例"]
        print(f"折价交易比例: {discount_ratio}%")
        
        if discount_ratio > 50:
            print("市场情绪: 偏悲观（折价交易占主导）")
        else:
            print("市场情绪: 偏乐观（溢价或平价交易较多）")
    
    print("\n详细分析请查看生成的报告文件。")

if __name__ == "__main__":
    main()