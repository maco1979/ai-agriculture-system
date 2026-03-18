# 智能供应链管理API接口
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from config.config import settings

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# 数据模型
class SupplierBase(BaseModel):
    """供应商基础模型"""
    name: str = Field(..., description="供应商名称")
    contact_person: str = Field(..., description="联系人")
    email: str = Field(..., description="邮箱")
    phone: str = Field(..., description="电话")
    address: str = Field(..., description="地址")
    category: str = Field(..., description="供应商类别")
    rating: float = Field(default=0.0, ge=0, le=5, description="供应商评分")


class SupplierCreate(SupplierBase):
    """创建供应商模型"""
    pass


class Supplier(SupplierBase):
    """供应商响应模型"""
    id: int = Field(..., description="供应商ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class InventoryItemBase(BaseModel):
    """库存项目基础模型"""
    product_id: str = Field(..., description="产品ID")
    product_name: str = Field(..., description="产品名称")
    quantity: int = Field(..., ge=0, description="库存数量")
    unit: str = Field(..., description="单位")
    location: str = Field(..., description="库存位置")
    min_stock_level: int = Field(..., ge=0, description="最小库存水平")
    max_stock_level: int = Field(..., ge=0, description="最大库存水平")


class InventoryItemCreate(InventoryItemBase):
    """创建库存项目模型"""
    pass


class InventoryItem(InventoryItemBase):
    """库存项目响应模型"""
    id: int = Field(..., description="库存项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    status: str = Field(..., description="库存状态")
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """订单基础模型"""
    supplier_id: int = Field(..., description="供应商ID")
    order_date: date = Field(..., description="订单日期")
    expected_delivery_date: date = Field(..., description="预计交付日期")
    status: str = Field(..., description="订单状态")
    total_amount: float = Field(..., ge=0, description="总金额")


class OrderCreate(OrderBase):
    """创建订单模型"""
    items: List[Dict[str, Any]] = Field(..., description="订单项目")


class Order(OrderBase):
    """订单响应模型"""
    id: int = Field(..., description="订单ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    items: List[Dict[str, Any]] = Field(..., description="订单项目")
    
    class Config:
        from_attributes = True


class LogisticsBase(BaseModel):
    """物流基础模型"""
    order_id: int = Field(..., description="订单ID")
    tracking_number: str = Field(..., description="跟踪号码")
    carrier: str = Field(..., description="承运商")
    status: str = Field(..., description="物流状态")
    estimated_delivery_date: date = Field(..., description="预计交付日期")


class LogisticsCreate(LogisticsBase):
    """创建物流模型"""
    pass


class Logistics(LogisticsBase):
    """物流响应模型"""
    id: int = Field(..., description="物流ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    current_location: Optional[str] = Field(None, description="当前位置")
    
    class Config:
        from_attributes = True


class DemandForecastRequest(BaseModel):
    """需求预测请求模型"""
    product_id: str = Field(..., description="产品ID")
    horizon: int = Field(default=30, ge=1, le=90, description="预测天数")
    include_historical: bool = Field(default=False, description="是否包含历史数据")


class DemandForecastResponse(BaseModel):
    """需求预测响应模型"""
    product_id: str = Field(..., description="产品ID")
    horizon: int = Field(..., description="预测天数")
    forecast: List[Dict[str, Any]] = Field(..., description="预测结果")
    model_used: str = Field(..., description="使用的模型")
    confidence_level: float = Field(..., description="置信水平")


class SupplierEvaluationResponse(BaseModel):
    """供应商评估响应模型"""
    supplier_id: int = Field(..., description="供应商ID")
    supplier_name: str = Field(..., description="供应商名称")
    overall_rating: float = Field(..., description="整体评分")
    criteria_ratings: Dict[str, float] = Field(..., description="各维度评分")
    risk_level: str = Field(..., description="风险等级")
    recommendations: List[str] = Field(..., description="建议")


# 模拟数据
mock_suppliers = [
    {
        "id": 1,
        "name": "ABC供应商",
        "contact_person": "张三",
        "email": "zhangsan@abc.com",
        "phone": "13800138001",
        "address": "北京市朝阳区",
        "category": "电子产品",
        "rating": 4.5,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "name": "DEF供应商",
        "contact_person": "李四",
        "email": "lisi@def.com",
        "phone": "13900139002",
        "address": "上海市浦东新区",
        "category": "原材料",
        "rating": 4.2,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

mock_inventory = [
    {
        "id": 1,
        "product_id": "PROD001",
        "product_name": "智能传感器",
        "quantity": 100,
        "unit": "个",
        "location": "仓库A-1区",
        "min_stock_level": 20,
        "max_stock_level": 200,
        "status": "正常",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "product_id": "PROD002",
        "product_name": "控制器",
        "quantity": 50,
        "unit": "个",
        "location": "仓库B-2区",
        "min_stock_level": 10,
        "max_stock_level": 100,
        "status": "正常",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]


# 供应商管理API
@router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    category: Optional[str] = Query(None, description="供应商类别")
):
    """获取供应商列表"""
    try:
        logger.info(f"获取供应商列表，skip={skip}, limit={limit}, category={category}")
        # 这里应该从数据库获取数据，现在返回模拟数据
        suppliers = mock_suppliers
        if category:
            suppliers = [s for s in suppliers if s["category"] == category]
        return suppliers[skip:skip+limit]
    except Exception as e:
        logger.error(f"获取供应商列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取供应商列表失败")


@router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: int):
    """获取供应商详情"""
    try:
        logger.info(f"获取供应商详情，ID={supplier_id}")
        # 这里应该从数据库获取数据，现在返回模拟数据
        supplier = next((s for s in mock_suppliers if s["id"] == supplier_id), None)
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")
        return supplier
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取供应商详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取供应商详情失败")


@router.post("/suppliers", response_model=Supplier, status_code=201)
async def create_supplier(supplier: SupplierCreate):
    """创建供应商"""
    try:
        logger.info(f"创建供应商: {supplier.name}")
        # 这里应该保存到数据库，现在返回模拟数据
        new_supplier = {
            "id": len(mock_suppliers) + 1,
            "name": supplier.name,
            "contact_person": supplier.contact_person,
            "email": supplier.email,
            "phone": supplier.phone,
            "address": supplier.address,
            "category": supplier.category,
            "rating": supplier.rating,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mock_suppliers.append(new_supplier)
        return new_supplier
    except Exception as e:
        logger.error(f"创建供应商失败: {e}")
        raise HTTPException(status_code=500, detail="创建供应商失败")


# 库存管理API
@router.get("/inventory", response_model=List[InventoryItem])
async def get_inventory(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    location: Optional[str] = Query(None, description="库存位置"),
    status: Optional[str] = Query(None, description="库存状态")
):
    """获取库存列表"""
    try:
        logger.info(f"获取库存列表，skip={skip}, limit={limit}, location={location}, status={status}")
        # 这里应该从数据库获取数据，现在返回模拟数据
        inventory = mock_inventory
        if location:
            inventory = [i for i in inventory if i["location"] == location]
        if status:
            inventory = [i for i in inventory if i["status"] == status]
        return inventory[skip:skip+limit]
    except Exception as e:
        logger.error(f"获取库存列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取库存列表失败")


@router.get("/inventory/{inventory_id}", response_model=InventoryItem)
async def get_inventory_item(inventory_id: int):
    """获取库存项目详情"""
    try:
        logger.info(f"获取库存项目详情，ID={inventory_id}")
        # 这里应该从数据库获取数据，现在返回模拟数据
        item = next((i for i in mock_inventory if i["id"] == inventory_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="库存项目不存在")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取库存项目详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取库存项目详情失败")


# 需求预测API
@router.post("/demand-forecast", response_model=DemandForecastResponse)
async def get_demand_forecast(request: DemandForecastRequest):
    """获取需求预测"""
    try:
        logger.info(f"获取需求预测，产品ID={request.product_id}, horizon={request.horizon}")
        # 这里应该调用预测模型，现在返回模拟数据
        forecast = []
        for i in range(request.horizon):
            forecast_date = date.today()
            forecast_date = forecast_date.replace(day=forecast_date.day + i)
            forecast.append({
                "date": forecast_date,
                "predicted_demand": 100 + i * 5 + (i % 7) * 10,
                "lower_bound": 80 + i * 4,
                "upper_bound": 120 + i * 6
            })
        
        return {
            "product_id": request.product_id,
            "horizon": request.horizon,
            "forecast": forecast,
            "model_used": settings.DEMAND_FORECAST_MODEL,
            "confidence_level": 0.95
        }
    except Exception as e:
        logger.error(f"获取需求预测失败: {e}")
        raise HTTPException(status_code=500, detail="获取需求预测失败")


# 供应商评估API
@router.get("/suppliers/{supplier_id}/evaluation", response_model=SupplierEvaluationResponse)
async def evaluate_supplier(supplier_id: int):
    """评估供应商"""
    try:
        logger.info(f"评估供应商，ID={supplier_id}")
        # 这里应该从数据库获取数据并进行评估，现在返回模拟数据
        supplier = next((s for s in mock_suppliers if s["id"] == supplier_id), None)
        if not supplier:
            raise HTTPException(status_code=404, detail="供应商不存在")
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "overall_rating": supplier["rating"],
            "criteria_ratings": {
                "产品质量": 4.5,
                "交付及时性": 4.2,
                "价格合理性": 3.8,
                "服务水平": 4.0,
                "响应速度": 4.3
            },
            "risk_level": "低" if supplier["rating"] >= 4.0 else "中",
            "recommendations": [
                "继续保持良好合作关系",
                "考虑增加采购量",
                "探索更多合作领域"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评估供应商失败: {e}")
        raise HTTPException(status_code=500, detail="评估供应商失败")


# 物流管理API
@router.get("/logistics/{tracking_number}")
async def track_logistics(tracking_number: str):
    """跟踪物流状态"""
    try:
        logger.info(f"跟踪物流状态，单号={tracking_number}")
        # 这里应该从物流系统获取数据，现在返回模拟数据
        return {
            "tracking_number": tracking_number,
            "status": "在途",
            "carrier": "顺丰速运",
            "current_location": "上海市浦东新区",
            "estimated_delivery_date": date.today().replace(day=date.today().day + 2),
            "events": [
                {
                    "timestamp": datetime.now().replace(hour=10, minute=30),
                    "location": "北京市朝阳区",
                    "description": "快件已发出"
                },
                {
                    "timestamp": datetime.now().replace(hour=14, minute=20),
                    "location": "上海市浦东新区",
                    "description": "快件已到达中转站"
                }
            ]
        }
    except Exception as e:
        logger.error(f"跟踪物流状态失败: {e}")
        raise HTTPException(status_code=500, detail="跟踪物流状态失败")


# 供应链优化API
@router.get("/optimization/recommendations")
async def get_optimization_recommendations():
    """获取供应链优化建议"""
    try:
        logger.info("获取供应链优化建议")
        # 这里应该调用优化算法，现在返回模拟数据
        return {
            "recommendations": [
                {
                    "type": "inventory",
                    "description": "库存水平优化",
                    "details": "建议降低PROD001的库存水平至80个，以减少库存成本",
                    "priority": "高"
                },
                {
                    "type": "supplier",
                    "description": "供应商优化",
                    "details": "建议与ABC供应商签订长期合作协议，以获得更优惠的价格",
                    "priority": "中"
                },
                {
                    "type": "logistics",
                    "description": "物流路线优化",
                    "details": "建议优化上海至北京的物流路线，预计可减少运输时间15%",
                    "priority": "中"
                }
            ],
            "potential_savings": 150000,
            "optimization_score": 0.75
        }
    except Exception as e:
        logger.error(f"获取供应链优化建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取供应链优化建议失败")
