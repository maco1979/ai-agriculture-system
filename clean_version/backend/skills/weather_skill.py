"""
天气查询技能 - 为决策引擎智能体提供天气数据
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WeatherSkill:
    """天气查询技能"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://wttr.in"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """
        获取天气预测
        
        Args:
            location: 地点（城市名或坐标）
            days: 预测天数（1-3）
        
        Returns:
            天气预测数据
        """
        try:
            url = f"{self.base_url}/{location}"
            params = {
                "format": "j1",
                "lang": "zh"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_weather_data(data, days)
                else:
                    logger.error(f"天气API请求失败: {response.status}")
                    return self._get_fallback_forecast(location, days)
                    
        except Exception as e:
            logger.error(f"获取天气数据失败: {e}")
            return self._get_fallback_forecast(location, days)
    
    async def get_current(self, location: str) -> Dict[str, Any]:
        """
        获取当前天气
        
        Args:
            location: 地点
        
        Returns:
            当前天气数据
        """
        try:
            url = f"{self.base_url}/{location}"
            params = {
                "format": "j1",
                "lang": "zh"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_current_weather(data)
                else:
                    logger.error(f"天气API请求失败: {response.status}")
                    return self._get_fallback_current(location)
                    
        except Exception as e:
            logger.error(f"获取当前天气失败: {e}")
            return self._get_fallback_current(location)
    
    async def get_agriculture_weather(self, location: str) -> Dict[str, Any]:
        """
        获取农业专用天气数据
        
        Args:
            location: 地点
        
        Returns:
            农业天气数据
        """
        forecast = await self.get_forecast(location, days=3)
        
        # 农业相关分析
        agriculture_analysis = {
            "suitable_for_planting": self._check_planting_suitability(forecast),
            "irrigation_recommendation": self._calculate_irrigation(forecast),
            "frost_risk": self._check_frost_risk(forecast),
            "pest_risk_level": self._calculate_pest_risk(forecast),
            "harvest_recommendation": self._check_harvest_time(forecast)
        }
        
        return {
            "forecast": forecast,
            "agriculture_analysis": agriculture_analysis
        }
    
    def _parse_weather_data(self, data: Dict, days: int) -> Dict[str, Any]:
        """解析天气数据"""
        try:
            current_condition = data.get("current_condition", [{}])[0]
            weather = data.get("weather", [])
            
            forecast_days = []
            for i in range(min(days, len(weather))):
                day_data = weather[i]
                forecast_days.append({
                    "date": day_data.get("date"),
                    "max_temp": float(day_data.get("maxtempC", 0)),
                    "min_temp": float(day_data.get("mintempC", 0)),
                    "condition": day_data.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", ""),
                    "precipitation": float(day_data.get("hourly", [{}])[0].get("precipMM", 0)),
                    "humidity": int(day_data.get("hourly", [{}])[0].get("humidity", 0)),
                    "wind_speed": float(day_data.get("hourly", [{}])[0].get("windspeedKmph", 0))
                })
            
            return {
                "location": data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", ""),
                "current": {
                    "temp": float(current_condition.get("temp_C", 0)),
                    "condition": current_condition.get("weatherDesc", [{}])[0].get("value", ""),
                    "humidity": int(current_condition.get("humidity", 0)),
                    "wind_speed": float(current_condition.get("windspeedKmph", 0)),
                    "precipitation": float(current_condition.get("precipMM", 0))
                },
                "forecast": forecast_days
            }
        except Exception as e:
            logger.error(f"解析天气数据失败: {e}")
            return self._get_fallback_forecast("unknown", days)
    
    def _parse_current_weather(self, data: Dict) -> Dict[str, Any]:
        """解析当前天气数据"""
        try:
            current_condition = data.get("current_condition", [{}])[0]
            return {
                "temperature": float(current_condition.get("temp_C", 0)),
                "condition": current_condition.get("weatherDesc", [{}])[0].get("value", ""),
                "humidity": int(current_condition.get("humidity", 0)),
                "wind_speed": float(current_condition.get("windspeedKmph", 0)),
                "wind_direction": current_condition.get("winddir16Point", ""),
                "precipitation": float(current_condition.get("precipMM", 0)),
                "pressure": float(current_condition.get("pressure", 0)),
                "visibility": float(current_condition.get("visibility", 0))
            }
        except Exception as e:
            logger.error(f"解析当前天气失败: {e}")
            return self._get_fallback_current("unknown")
    
    def _check_planting_suitability(self, forecast: Dict) -> bool:
        """检查是否适合种植"""
        try:
            # 简单规则：未来3天无大雨，温度适宜
            suitable_days = 0
            for day in forecast.get("forecast", []):
                temp = day.get("max_temp", 0)
                precip = day.get("precipitation", 0)
                
                if 15 <= temp <= 30 and precip < 10:
                    suitable_days += 1
            
            return suitable_days >= 2
        except:
            return True
    
    def _calculate_irrigation(self, forecast: Dict) -> str:
        """计算灌溉建议"""
        try:
            total_precip = sum(day.get("precipitation", 0) for day in forecast.get("forecast", []))
            
            if total_precip > 20:
                return "未来几天有充足降雨，无需灌溉"
            elif total_precip > 10:
                return "降雨量适中，可减少灌溉"
            else:
                return "降雨不足，建议正常灌溉"
        except:
            return "根据土壤湿度决定灌溉"
    
    def _check_frost_risk(self, forecast: Dict) -> str:
        """检查霜冻风险"""
        try:
            min_temps = [day.get("min_temp", 0) for day in forecast.get("forecast", [])]
            if any(temp < 0 for temp in min_temps):
                return "高风险：有霜冻可能"
            elif any(temp < 5 for temp in min_temps):
                return "中风险：低温警告"
            else:
                return "低风险：无霜冻"
        except:
            return "无法评估霜冻风险"
    
    def _calculate_pest_risk(self, forecast: Dict) -> str:
        """计算病虫害风险"""
        try:
            # 基于温度和湿度评估
            risk_score = 0
            for day in forecast.get("forecast", []):
                temp = day.get("max_temp", 0)
                humidity = day.get("humidity", 0)
                
                # 适宜病虫害的温度和湿度
                if 20 <= temp <= 30 and humidity > 70:
                    risk_score += 2
                elif 15 <= temp <= 35 and humidity > 60:
                    risk_score += 1
            
            if risk_score >= 4:
                return "高风险"
            elif risk_score >= 2:
                return "中风险"
            else:
                return "低风险"
        except:
            return "无法评估病虫害风险"
    
    def _check_harvest_time(self, forecast: Dict) -> str:
        """检查收获时间建议"""
        try:
            # 检查未来3天天气是否适合收获
            suitable_days = 0
            for day in forecast.get("forecast", []):
                precip = day.get("precipitation", 0)
                wind = day.get("wind_speed", 0)
                
                if precip < 5 and wind < 20:
                    suitable_days += 1
            
            if suitable_days >= 2:
                return "未来几天天气适宜收获"
            else:
                return "建议等待更好天气"
        except:
            return "根据作物成熟度决定收获时间"
    
    def _get_fallback_forecast(self, location: str, days: int) -> Dict[str, Any]:
        """获取备用预测数据"""
        now = datetime.now()
        forecast_days = []
        
        for i in range(days):
            date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
            forecast_days.append({
                "date": date,
                "max_temp": 25.0,
                "min_temp": 15.0,
                "condition": "晴天",
                "precipitation": 0.0,
                "humidity": 60,
                "wind_speed": 10.0
            })
        
        return {
            "location": location,
            "current": {
                "temp": 20.0,
                "condition": "晴天",
                "humidity": 60,
                "wind_speed": 10.0,
                "precipitation": 0.0
            },
            "forecast": forecast_days
        }
    
    def _get_fallback_current(self, location: str) -> Dict[str, Any]:
        """获取备用当前天气数据"""
        return {
            "temperature": 20.0,
            "condition": "晴天",
            "humidity": 60,
            "wind_speed": 10.0,
            "wind_direction": "东北风",
            "precipitation": 0.0,
            "pressure": 1013.0,
            "visibility": 10.0
        }


# 使用示例
async def example_usage():
    """使用示例"""
    async with WeatherSkill() as weather:
        # 获取天气预报
        forecast = await weather.get_forecast("北京", days=3)
        print("天气预报:", forecast)
        
        # 获取农业天气分析
        agri_weather = await weather.get_agriculture_weather("北京")
        print("农业天气分析:", agri_weather)


if __name__ == "__main__":
    asyncio.run(example_usage())