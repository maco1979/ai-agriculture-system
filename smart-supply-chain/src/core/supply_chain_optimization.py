# 供应链优化核心模块
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import random

from config.config import settings

# 配置日志
logger = logging.getLogger(__name__)


class SupplyChainOptimizer:
    """供应链优化器"""
    
    def __init__(self):
        """初始化供应链优化器"""
        logger.info("初始化供应链优化器")
        self.demand_forecaster = DemandForecaster()
        self.supplier_evaluator = SupplierEvaluator()
        self.inventory_optimizer = InventoryOptimizer()
        self.logistics_optimizer = LogisticsOptimizer()
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """获取供应链优化建议"""
        try:
            logger.info("获取供应链优化建议")
            
            # 收集各模块的优化建议
            inventory_recommendations = self.inventory_optimizer.get_recommendations()
            supplier_recommendations = self.supplier_evaluator.get_recommendations()
            logistics_recommendations = self.logistics_optimizer.get_recommendations()
            
            # 合并建议
            recommendations = []
            recommendations.extend(inventory_recommendations)
            recommendations.extend(supplier_recommendations)
            recommendations.extend(logistics_recommendations)
            
            # 计算潜在节省
            potential_savings = sum([rec.get("potential_savings", 0) for rec in recommendations])
            
            # 计算优化评分
            optimization_score = self._calculate_optimization_score(recommendations)
            
            return {
                "recommendations": recommendations,
                "potential_savings": potential_savings,
                "optimization_score": optimization_score
            }
        except Exception as e:
            logger.error(f"获取供应链优化建议失败: {e}")
            raise
    
    def _calculate_optimization_score(self, recommendations: List[Dict[str, Any]]) -> float:
        """计算优化评分"""
        # 基于建议数量、优先级和潜在节省计算评分
        if not recommendations:
            return 1.0
        
        priority_scores = {
            "高": 3,
            "中": 2,
            "低": 1
        }
        
        total_score = sum([priority_scores.get(rec.get("priority", "低"), 1) for rec in recommendations])
        max_possible_score = len(recommendations) * 3
        
        return min(1.0, total_score / max_possible_score)


class DemandForecaster:
    """需求预测器"""
    
    def __init__(self):
        """初始化需求预测器"""
        logger.info("初始化需求预测器")
        # 存储历史需求数据
        self.historical_data = {}
        # 存储预测模型参数
        self.model_params = {}
    
    def add_historical_data(self, product_id: str, data: List[Dict[str, Any]]):
        """添加历史需求数据
        
        Args:
            product_id: 产品ID
            data: 历史需求数据，格式为[{"date": date, "demand": float}, ...]
        """
        if product_id not in self.historical_data:
            self.historical_data[product_id] = []
        
        # 添加并按日期排序
        self.historical_data[product_id].extend(data)
        self.historical_data[product_id].sort(key=lambda x: x['date'])
        
        logger.info(f"为产品 {product_id} 添加了 {len(data)} 条历史需求数据")
    
    def generate_synthetic_data(self, product_id: str, days: int = 180) -> List[Dict[str, Any]]:
        """生成合成历史数据
        
        Args:
            product_id: 产品ID
            days: 生成天数
            
        Returns:
            合成历史数据
        """
        data = []
        start_date = date.today() - timedelta(days=days)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # 基础需求
            base_demand = 100
            
            # 趋势
            trend = i * 0.2
            
            # 季节性（周度）
            weekday = current_date.weekday()
            if weekday in [0, 4]:  # 周一和周五
                seasonal = 20
            elif weekday in [1, 3]:  # 周二和周四
                seasonal = 10
            else:  # 周三、周六、周日
                seasonal = 5
            
            # 月度季节性
            month = current_date.month
            if month in [12, 1, 2]:  # 冬季
                monthly_seasonal = 15
            elif month in [6, 7, 8]:  # 夏季
                monthly_seasonal = 10
            else:  # 春秋季
                monthly_seasonal = 5
            
            # 随机因素
            random_factor = random.randint(-15, 15)
            
            # 计算总需求
            demand = base_demand + trend + seasonal + monthly_seasonal + random_factor
            demand = max(0, demand)
            
            data.append({
                "date": current_date,
                "demand": demand
            })
        
        # 存储合成数据
        self.add_historical_data(product_id, data)
        return data
    
    def moving_average_forecast(self, product_id: str, horizon: int, window: int = 7) -> List[Dict[str, Any]]:
        """基于移动平均的需求预测
        
        Args:
            product_id: 产品ID
            horizon: 预测 horizon
            window: 移动平均窗口大小
            
        Returns:
            预测结果
        """
        # 确保有历史数据
        if product_id not in self.historical_data or not self.historical_data[product_id]:
            self.generate_synthetic_data(product_id)
        
        historical = self.historical_data[product_id]
        
        # 计算移动平均
        forecast = []
        last_date = historical[-1]['date']
        
        # 计算最近window天的平均值
        recent_demands = [h['demand'] for h in historical[-window:]]
        avg_demand = sum(recent_demands) / len(recent_demands)
        
        # 计算需求波动性
        if len(recent_demands) > 1:
            mean = avg_demand
            variance = sum((d - mean) ** 2 for d in recent_demands) / len(recent_demands)
            std_dev = variance ** 0.5
        else:
            std_dev = avg_demand * 0.1
        
        # 生成预测
        for i in range(horizon):
            forecast_date = last_date + timedelta(days=i+1)
            
            # 考虑周度季节性
            weekday = forecast_date.weekday()
            if weekday in [0, 4]:  # 周一和周五
                seasonal_factor = 1.2
            elif weekday in [1, 3]:  # 周二和周四
                seasonal_factor = 1.1
            else:  # 周三、周六、周日
                seasonal_factor = 0.9
            
            predicted_demand = avg_demand * seasonal_factor
            lower_bound = predicted_demand - std_dev
            upper_bound = predicted_demand + std_dev
            
            forecast.append({
                "date": forecast_date,
                "predicted_demand": max(0, predicted_demand),
                "lower_bound": max(0, lower_bound),
                "upper_bound": max(0, upper_bound),
                "method": "moving_average"
            })
        
        return forecast
    
    def exponential_smoothing_forecast(self, product_id: str, horizon: int, alpha: float = 0.3) -> List[Dict[str, Any]]:
        """基于指数平滑的需求预测
        
        Args:
            product_id: 产品ID
            horizon: 预测 horizon
            alpha: 平滑参数
            
        Returns:
            预测结果
        """
        # 确保有历史数据
        if product_id not in self.historical_data or not self.historical_data[product_id]:
            self.generate_synthetic_data(product_id)
        
        historical = self.historical_data[product_id]
        
        # 计算指数平滑
        forecast = []
        last_date = historical[-1]['date']
        
        # 初始化平滑值
        smoothed = historical[0]['demand']
        for i in range(1, len(historical)):
            demand = historical[i]['demand']
            smoothed = alpha * demand + (1 - alpha) * smoothed
        
        # 计算需求波动性
        demands = [h['demand'] for h in historical]
        mean = sum(demands) / len(demands)
        variance = sum((d - mean) ** 2 for d in demands) / len(demands)
        std_dev = variance ** 0.5
        
        # 生成预测
        for i in range(horizon):
            forecast_date = last_date + timedelta(days=i+1)
            
            # 考虑周度季节性
            weekday = forecast_date.weekday()
            if weekday in [0, 4]:  # 周一和周五
                seasonal_factor = 1.2
            elif weekday in [1, 3]:  # 周二和周四
                seasonal_factor = 1.1
            else:  # 周三、周六、周日
                seasonal_factor = 0.9
            
            predicted_demand = smoothed * seasonal_factor
            lower_bound = predicted_demand - std_dev
            upper_bound = predicted_demand + std_dev
            
            forecast.append({
                "date": forecast_date,
                "predicted_demand": max(0, predicted_demand),
                "lower_bound": max(0, lower_bound),
                "upper_bound": max(0, upper_bound),
                "method": "exponential_smoothing"
            })
        
        return forecast
    
    def forecast_demand(self, product_id: str, horizon: int, method: str = "hybrid") -> List[Dict[str, Any]]:
        """预测需求
        
        Args:
            product_id: 产品ID
            horizon: 预测 horizon
            method: 预测方法 (moving_average, exponential_smoothing, hybrid)
            
        Returns:
            预测结果
        """
        try:
            logger.info(f"预测需求，产品ID={product_id}, horizon={horizon}, method={method}")
            
            if method == "moving_average":
                return self.moving_average_forecast(product_id, horizon)
            elif method == "exponential_smoothing":
                return self.exponential_smoothing_forecast(product_id, horizon)
            else:  # hybrid
                # 结合两种方法
                ma_forecast = self.moving_average_forecast(product_id, horizon)
                es_forecast = self.exponential_smoothing_forecast(product_id, horizon)
                
                # 加权平均
                hybrid_forecast = []
                for ma, es in zip(ma_forecast, es_forecast):
                    predicted_demand = (ma["predicted_demand"] * 0.5 + es["predicted_demand"] * 0.5)
                    lower_bound = min(ma["lower_bound"], es["lower_bound"])
                    upper_bound = max(ma["upper_bound"], es["upper_bound"])
                    
                    hybrid_forecast.append({
                        "date": ma["date"],
                        "predicted_demand": max(0, predicted_demand),
                        "lower_bound": max(0, lower_bound),
                        "upper_bound": max(0, upper_bound),
                        "method": "hybrid"
                    })
                
                return hybrid_forecast
        except Exception as e:
            logger.error(f"预测需求失败: {e}")
            raise
    
    def get_demand_insights(self, product_id: str, historical_days: int = 90) -> Dict[str, Any]:
        """获取需求洞察"""
        try:
            logger.info(f"获取需求洞察，产品ID={product_id}")
            
            # 确保有历史数据
            if product_id not in self.historical_data or not self.historical_data[product_id]:
                self.generate_synthetic_data(product_id)
            
            historical = self.historical_data[product_id]
            
            # 分析历史数据
            recent_data = historical[-historical_days:] if len(historical) >= historical_days else historical
            
            # 计算趋势
            if len(recent_data) >= 2:
                first_demand = recent_data[0]['demand']
                last_demand = recent_data[-1]['demand']
                if last_demand > first_demand * 1.1:
                    trend = "上升"
                elif last_demand < first_demand * 0.9:
                    trend = "下降"
                else:
                    trend = "稳定"
            else:
                trend = "稳定"
            
            # 分析周度模式
            weekday_demands = {i: [] for i in range(7)}
            for data in recent_data:
                weekday = data['date'].weekday()
                weekday_demands[weekday].append(data['demand'])
            
            # 计算每天的平均需求
            weekday_averages = {i: sum(demands) / len(demands) if demands else 0 for i, demands in weekday_demands.items()}
            
            # 找出 peak periods
            peak_periods = []
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            sorted_weekdays = sorted(weekday_averages.items(), key=lambda x: x[1], reverse=True)
            for weekday, avg_demand in sorted_weekdays[:2]:
                peak_periods.append(weekdays[weekday])
            
            # 计算平均需求
            avg_demand = sum(data['demand'] for data in recent_data) / len(recent_data)
            
            # 计算需求波动性（变异系数）
            demands = [data['demand'] for data in recent_data]
            mean = avg_demand
            variance = sum((d - mean) ** 2 for d in demands) / len(demands)
            std_dev = variance ** 0.5
            volatility = std_dev / mean if mean > 0 else 0
            
            # 生成建议
            recommendations = []
            if trend == "上升":
                recommendations.append("需求呈上升趋势，建议增加库存水平")
            elif trend == "下降":
                recommendations.append("需求呈下降趋势，建议减少库存水平")
            
            if volatility > 0.2:
                recommendations.append("需求波动性较大，建议增加安全库存")
            
            if peak_periods:
                recommendations.append(f"在{peak_periods[0]}和{peak_periods[1]}增加库存水平")
            
            recommendations.append("优化补货周期以应对周度波动")
            
            return {
                "product_id": product_id,
                "historical_trend": trend,
                "seasonal_pattern": "周度",
                "peak_periods": peak_periods,
                "average_demand": round(avg_demand, 2),
                "demand_volatility": round(volatility, 3),
                "weekday_averages": {weekdays[i]: round(avg, 2) for i, avg in weekday_averages.items()},
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"获取需求洞察失败: {e}")
            raise
    
    def evaluate_forecast_accuracy(self, product_id: str, horizon: int = 7) -> Dict[str, float]:
        """评估预测准确性
        
        Args:
            product_id: 产品ID
            horizon: 评估 horizon
            
        Returns:
            评估指标
        """
        try:
            # 确保有历史数据
            if product_id not in self.historical_data or len(self.historical_data[product_id]) < horizon:
                self.generate_synthetic_data(product_id, days=horizon * 2)
            
            historical = self.historical_data[product_id]
            
            # 分割数据：用前n-horizon天预测后horizon天
            train_data = historical[:-horizon]
            test_data = historical[-horizon:]
            
            # 保存原始历史数据
            original_data = self.historical_data[product_id].copy()
            
            # 临时修改历史数据以进行预测
            self.historical_data[product_id] = train_data
            
            # 进行预测
            forecast = self.forecast_demand(product_id, horizon)
            
            # 恢复原始历史数据
            self.historical_data[product_id] = original_data
            
            # 计算评估指标
            actuals = [data['demand'] for data in test_data]
            predictions = [f['predicted_demand'] for f in forecast]
            
            # 平均绝对误差 (MAE)
            mae = sum(abs(a - p) for a, p in zip(actuals, predictions)) / len(actuals)
            
            # 平均绝对百分比误差 (MAPE)
            mape = sum(abs((a - p) / a) for a, p in zip(actuals, predictions) if a > 0) / len(actuals)
            
            # 均方根误差 (RMSE)
            rmse = (sum((a - p) ** 2 for a, p in zip(actuals, predictions)) / len(actuals)) ** 0.5
            
            # 对称平均绝对百分比误差 (sMAPE)
            smape = sum(2 * abs(a - p) / (abs(a) + abs(p)) for a, p in zip(actuals, predictions) if abs(a) + abs(p) > 0) / len(actuals)
            
            return {
                "mae": round(mae, 2),
                "mape": round(mape, 4),
                "rmse": round(rmse, 2),
                "smape": round(smape, 4)
            }
        except Exception as e:
            logger.error(f"评估预测准确性失败: {e}")
            raise


class SupplierEvaluator:
    """供应商评估器"""
    
    def __init__(self):
        """初始化供应商评估器"""
        logger.info("初始化供应商评估器")
    
    def evaluate_supplier(self, supplier_id: int) -> Dict[str, Any]:
        """评估供应商"""
        try:
            logger.info(f"评估供应商，ID={supplier_id}")
            
            # 这里应该从数据库获取供应商数据并进行评估
            # 现在返回模拟数据
            return {
                "supplier_id": supplier_id,
                "supplier_name": f"供应商{supplier_id}",
                "overall_rating": random.uniform(3.5, 4.8),
                "criteria_ratings": {
                    "产品质量": random.uniform(3.8, 5.0),
                    "交付及时性": random.uniform(3.5, 4.8),
                    "价格合理性": random.uniform(3.0, 4.5),
                    "服务水平": random.uniform(3.2, 4.7),
                    "响应速度": random.uniform(3.0, 4.9)
                },
                "risk_level": random.choice(["低", "中", "低", "低"]),
                "recommendations": [
                    "继续保持良好合作关系",
                    "考虑增加采购量",
                    "探索更多合作领域"
                ]
            }
        except Exception as e:
            logger.error(f"评估供应商失败: {e}")
            raise
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取供应商优化建议"""
        try:
            logger.info("获取供应商优化建议")
            
            # 这里应该基于供应商评估结果生成建议
            # 现在返回模拟数据
            return [
                {
                    "type": "supplier",
                    "description": "供应商优化",
                    "details": "建议与ABC供应商签订长期合作协议，以获得更优惠的价格",
                    "priority": "中",
                    "potential_savings": 50000
                },
                {
                    "type": "supplier",
                    "description": "供应商多样化",
                    "details": "建议增加1-2家备选供应商，降低供应链风险",
                    "priority": "中",
                    "potential_savings": 30000
                }
            ]
        except Exception as e:
            logger.error(f"获取供应商优化建议失败: {e}")
            raise


class InventoryOptimizer:
    """库存优化器"""
    
    def __init__(self):
        """初始化库存优化器"""
        logger.info("初始化库存优化器")
    
    def optimize_inventory_levels(self, product_id: str) -> Dict[str, Any]:
        """优化库存水平"""
        try:
            logger.info(f"优化库存水平，产品ID={product_id}")
            
            # 这里应该基于需求预测和成本数据优化库存水平
            # 现在返回模拟数据
            return {
                "product_id": product_id,
                "current_level": 100,
                "optimal_level": 80,
                "safety_stock": 20,
                "reorder_point": 40,
                "economic_order_quantity": 60,
                "potential_savings": 20000,
                "recommendations": [
                    f"将{product_id}的库存水平调整至80个",
                    "设置40个的再订购点",
                    "采用60个的经济订购批量"
                ]
            }
        except Exception as e:
            logger.error(f"优化库存水平失败: {e}")
            raise
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取库存优化建议"""
        try:
            logger.info("获取库存优化建议")
            
            # 这里应该基于库存分析结果生成建议
            # 现在返回模拟数据
            return [
                {
                    "type": "inventory",
                    "description": "库存水平优化",
                    "details": "建议降低PROD001的库存水平至80个，以减少库存成本",
                    "priority": "高",
                    "potential_savings": 40000
                },
                {
                    "type": "inventory",
                    "description": "库存周转率优化",
                    "details": "建议优化PROD002的补货周期，提高库存周转率",
                    "priority": "中",
                    "potential_savings": 20000
                }
            ]
        except Exception as e:
            logger.error(f"获取库存优化建议失败: {e}")
            raise


class LogisticsOptimizer:
    """物流优化器"""
    
    def __init__(self):
        """初始化物流优化器"""
        logger.info("初始化物流优化器")
    
    def optimize_route(self, origin: str, destination: str, weight: float) -> Dict[str, Any]:
        """优化物流路线"""
        try:
            logger.info(f"优化物流路线，从{origin}到{destination}")
            
            # 这里应该调用路线优化算法
            # 现在返回模拟数据
            return {
                "origin": origin,
                "destination": destination,
                "optimal_route": [origin, "中转站1", "中转站2", destination],
                "estimated_distance": random.uniform(500, 2000),
                "estimated_time": random.uniform(12, 48),
                "estimated_cost": random.uniform(1000, 5000),
                "savings": random.uniform(500, 2000),
                "recommendations": [
                    f"采用优化路线，预计可节省{random.uniform(5, 15):.1f}%的运输时间",
                    "考虑采用拼箱运输以降低成本",
                    "优化发货时间以避开高峰期"
                ]
            }
        except Exception as e:
            logger.error(f"优化物流路线失败: {e}")
            raise
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取物流优化建议"""
        try:
            logger.info("获取物流优化建议")
            
            # 这里应该基于物流分析结果生成建议
            # 现在返回模拟数据
            return [
                {
                    "type": "logistics",
                    "description": "物流路线优化",
                    "details": "建议优化上海至北京的物流路线，预计可减少运输时间15%",
                    "priority": "中",
                    "potential_savings": 30000
                },
                {
                    "type": "logistics",
                    "description": "运输方式优化",
                    "details": "建议对重量超过500kg的货物采用铁路运输，以降低成本",
                    "priority": "低",
                    "potential_savings": 10000
                }
            ]
        except Exception as e:
            logger.error(f"获取物流优化建议失败: {e}")
            raise
