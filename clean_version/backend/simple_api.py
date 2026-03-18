"""
完全独立的简化版API应用
不依赖任何AI框架，只提供auth、community和agriculture接口
"""

from fastapi import FastAPI, HTTPException, status, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
import asyncio
import base64
import math
import struct
import zlib
import os
import sys
import threading
import time
from datetime import datetime, timedelta

# ── 尝试导入 cv2（OpenCV），失败时回退纯模拟 ──────────────────────────────
try:
    import cv2 as _cv2
    _CV2_AVAILABLE = True
except ImportError:
    _cv2 = None
    _CV2_AVAILABLE = False

# ── 尝试导入 CameraController（真实摄像头控制器）────────────────────────────
_CameraController = None
try:
    _backend_src = os.path.join(os.path.dirname(__file__), 'src')
    if _backend_src not in sys.path:
        sys.path.insert(0, _backend_src)
    from core.services.camera_controller import CameraController as _CameraController
    print(f"[Camera] CameraController 加载成功，src路径: {_backend_src}")
except Exception as _e:
    import traceback as _tb
    print(f"[Camera] CameraController 加载失败，降级为模拟模式: {_e}")
    _tb.print_exc()
    _CameraController = None

# ── 尝试导入 PTZCameraController（云台控制器）────────────────────────────────
_PTZCameraController = None
_PTZProtocol = None
_PTZAction = None
try:
    _backend_src_ptz = os.path.join(os.path.dirname(__file__), 'src')
    if _backend_src_ptz not in sys.path:
        sys.path.insert(0, _backend_src_ptz)
    from core.services.ptz_camera_controller import (
        PTZCameraController as _PTZCameraController,
        PTZProtocol as _PTZProtocol,
        PTZAction as _PTZAction,
    )
    print(f"[PTZ] PTZCameraController 加载成功")
except Exception as _e_ptz:
    import traceback as _tb_ptz
    print(f"[PTZ] PTZCameraController 加载失败: {_e_ptz}")
    _tb_ptz.print_exc()
    _PTZCameraController = None
    _PTZProtocol = None
    _PTZAction = None

# --------------------------
# 认证相关代码
# --------------------------
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

# --------------------------
# 农业AI相关代码
# --------------------------
agriculture_router = APIRouter(prefix="/api/agriculture", tags=["agriculture"])

# 模拟作物配置数据
crop_configs = {
    "番茄": {
        "growth_stages": [
            {"stage_name": "苗期", "duration_days": 20, "optimal_temperature": "20-25", "optimal_humidity": "60-70", "light_hours": 16},
            {"stage_name": "开花期", "duration_days": 30, "optimal_temperature": "22-28", "optimal_humidity": "50-60", "light_hours": 14},
            {"stage_name": "结果期", "duration_days": 40, "optimal_temperature": "25-30", "optimal_humidity": "50-60", "light_hours": 12}
        ],
        "target_yield": "高产量",
        "quality_metrics": ["甜度", "色泽", "大小"]
    },
    "生菜": {
        "growth_stages": [
            {"stage_name": "苗期", "duration_days": 15, "optimal_temperature": "18-22", "optimal_humidity": "70-80", "light_hours": 14},
            {"stage_name": "生长期", "duration_days": 25, "optimal_temperature": "20-25", "optimal_humidity": "60-70", "light_hours": 12}
        ],
        "target_yield": "高品质",
        "quality_metrics": ["嫩度", "颜色", "口感"]
    },
    "黄瓜": {
        "growth_stages": [
            {"stage_name": "苗期", "duration_days": 18, "optimal_temperature": "22-26", "optimal_humidity": "65-75", "light_hours": 16},
            {"stage_name": "开花期", "duration_days": 25, "optimal_temperature": "24-28", "optimal_humidity": "60-70", "light_hours": 14},
            {"stage_name": "结果期", "duration_days": 35, "optimal_temperature": "26-30", "optimal_humidity": "55-65", "light_hours": 12}
        ],
        "target_yield": "高产量",
        "quality_metrics": ["长度", "直径", "口感"]
    }
}

class LightRecipeRequest(BaseModel):
    """光配方请求"""
    crop_type: str
    current_day: int
    target_objective: str
    environment: Dict[str, float]

class PlantGrowthRequest(BaseModel):
    """植物生长预测请求"""
    crop_type: str
    current_day: int
    environmental_data: Dict[str, float]
    spectrum_data: List[float]

class CropPlanningRequest(BaseModel):
    """种植规划请求"""
    crop_type: str
    target_yield: str
    start_date: str
    expected_harvest_date: str

@agriculture_router.get("/crop-configs")
async def get_available_crops():
    """获取可用的作物配置"""
    return {
        "success": True,
        "data": crop_configs
    }

@agriculture_router.post("/light-recipe")
async def generate_light_recipe(request: LightRecipeRequest):
    """生成光配方"""
    # 模拟光配方生成
    recipe = {
        "uv_380nm": 0.05,
        "far_red_720nm": 0.1,
        "white_light": 0.7,
        "red_660nm": 0.15,
        "white_red_ratio": 4.67
    }
    
    # 根据目标调整配方
    if request.target_objective == "最大化产量":
        recipe["white_light"] = 0.75
        recipe["red_660nm"] = 0.15
    elif request.target_objective == "提升甜度":
        recipe["uv_380nm"] = 0.08
        recipe["white_light"] = 0.65
    
    return {
        "success": True,
        "data": {
            "recipe": recipe,
            "current_stage": "生长期",
            "light_hours": 14,
            "recommendations": ["保持当前光照强度", "注意温度控制"]
        }
    }

@agriculture_router.post("/growth-prediction")
async def predict_plant_growth(request: PlantGrowthRequest):
    """预测植物生长状态"""
    return {
        "success": True,
        "data": {
            "growth_rate": 0.85,
            "health_score": 92,
            "yield_potential": 0.88
        }
    }

@agriculture_router.post("/crop-planning")
async def plan_crop_growth(request: CropPlanningRequest):
    """制定种植计划"""
    if request.crop_type not in crop_configs:
        raise HTTPException(status_code=400, detail=f"不支持的作物类型: {request.crop_type}")
    
    crop_config = crop_configs[request.crop_type]
    total_days = sum(stage["duration_days"] for stage in crop_config["growth_stages"])
    
    planting_plan = []
    current_day = 0
    
    for stage in crop_config["growth_stages"]:
        planting_plan.append({
            "stage": stage["stage_name"],
            "start_day": current_day,
            "end_day": current_day + stage["duration_days"],
            "light_hours": stage["light_hours"],
            "temperature_range": stage["optimal_temperature"],
            "humidity_range": stage["optimal_humidity"],
            "key_activities": ["日常管理", "生长监测"]
        })
        current_day += stage["duration_days"]
    
    return {
        "success": True,
        "data": {
            "crop_type": request.crop_type,
            "total_days": total_days,
            "target_yield": request.target_yield,
            "planting_plan": planting_plan
        }
    }

@agriculture_router.get("/recommendations/{crop_type}")
async def get_growth_recommendations(crop_type: str, current_day: int = 0):
    """获取生长建议"""
    if crop_type not in crop_configs:
        raise HTTPException(status_code=400, detail=f"不支持的作物类型: {crop_type}")
    
    return {
        "success": True,
        "data": {
            "crop_type": crop_type,
            "current_stage": "生长期",
            "current_day": current_day,
            "recommendations": ["保持适宜温度", "定期浇水", "注意通风"],
            "next_stage": {
                "stage_name": "开花期",
                "days_until": 10,
                "preparation_tips": ["增加营养供应", "调整光照时间"]
            }
        }
    }

# 模拟用户积分数据
user_photon_points = {}

@agriculture_router.post("/contribute-data")
async def contribute_agriculture_data(data: Dict[str, Any]):
    """贡献农业数据并获得光子积分"""
    user_id = data.get("user_id", "anonymous")
    crop_type = data.get("crop_type", "unknown")
    growth_data = data.get("growth_data", {})
    
    # 计算获得的光子积分
    base_points = 10
    bonus_points = 0
    
    # 根据数据完整性给予额外奖励
    if growth_data.get("environment"):
        bonus_points += 5
    if growth_data.get("recipe"):
        bonus_points += 5
    if growth_data.get("day"):
        bonus_points += 2
    
    total_points = base_points + bonus_points
    
    # 更新用户积分
    if user_id not in user_photon_points:
        user_photon_points[user_id] = 0
    user_photon_points[user_id] += total_points
    
    # 记录贡献
    contribution_record = {
        "id": f"contrib_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "crop_type": crop_type,
        "growth_data": growth_data,
        "photon_points_earned": total_points,
        "total_points": user_photon_points[user_id],
        "contributed_at": datetime.now().isoformat()
    }
    
    return {
        "success": True,
        "data": {
            "message": "数据贡献成功！",
            "photon_points_earned": total_points,
            "total_points": user_photon_points[user_id],
            "contribution_id": contribution_record["id"]
        }
    }

@agriculture_router.get("/user-points/{user_id}")
async def get_user_photon_points(user_id: str):
    """获取用户光子积分"""
    points = user_photon_points.get(user_id, 0)
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "photon_points": points
        }
    }

@agriculture_router.post("/contribute-data")
async def contribute_agriculture_data(data: Dict[str, Any]):
    """贡献农业数据"""
    return {
        "success": True,
        "data": {
            "message": "数据贡献成功，感谢您的参与！",
            "contribution_id": str(uuid.uuid4()),
            "data_type": data.get("data_type", "unknown"),
            "points_earned": 50,
            "submitted_at": datetime.now().isoformat()
        }
    }

# 模拟存储扫码登录会话
qr_login_sessions: Dict[str, Dict[str, Any]] = {}

# 模拟用户数据
users_db: Dict[str, Dict[str, Any]] = {
    "wechat_user_1": {
        "id": "wechat_user_1",
        "username": "微信用户1",
        "avatar": "https://example.com/avatar1.jpg",
        "source": "wechat",
        "created_at": datetime.now().isoformat()
    },
    "alipay_user_1": {
        "id": "alipay_user_1",
        "username": "支付宝用户1",
        "avatar": "https://example.com/avatar2.jpg",
        "source": "alipay",
        "created_at": datetime.now().isoformat()
    },
    "test_user": {
        "id": "test_user",
        "username": "测试用户",
        "email": "test@example.com",
        "password": "test123456",  # 测试密码
        "avatar": "https://example.com/test_avatar.jpg",
        "source": "local",
        "role": "admin",
        "created_at": datetime.now().isoformat()
    }
}

class QRLoginResponse(BaseModel):
    """扫码登录响应模型"""
    qr_id: str
    qr_code_url: str
    expires_in: int
    created_at: str

class QRLoginStatusResponse(BaseModel):
    """扫码登录状态响应模型"""
    qr_id: str
    status: str  # "pending", "scanned", "confirmed", "expired"
    user_info: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"

class QRCallbackRequest(BaseModel):
    """扫码回调请求模型"""
    qr_id: str
    user_id: str
    source: str  # "wechat", "alipay"
    action: str  # "scan", "confirm", "cancel"

class PasswordLoginRequest(BaseModel):
    """密码登录请求模型"""
    email: str
    password: str

class CodeRegistrationRequest(BaseModel):
    """产品注册码注册请求模型"""
    code: str
    email: str
    password: str

# 模拟产品注册码数据库
product_codes = {
    "AGRI-PRO-2024-0001": {"status": "unused", "type": "pro"},
    "AGRI-PRO-2024-0002": {"status": "unused", "type": "pro"},
    "AGRI-BASIC-2024-0001": {"status": "unused", "type": "basic"},
    "AGRI-BASIC-2024-0002": {"status": "used", "type": "basic"}
}

@auth_router.post("/qr/generate", response_model=QRLoginResponse, status_code=status.HTTP_200_OK)
def generate_qr_code():
    """
    生成扫码登录的二维码
    返回二维码ID和二维码URL（实际应用中应返回真实的二维码图片数据）
    """
    qr_id = str(uuid.uuid4())
    expires_in = 300  # 5分钟过期
    created_at = datetime.now()
    expires_at = created_at + timedelta(seconds=expires_in)
    
    # 保存会话信息
    qr_login_sessions[qr_id] = {
        "status": "pending",  # pending: 等待扫码, scanned: 已扫码, confirmed: 已确认, expired: 已过期
        "created_at": created_at,
        "expires_at": expires_at,
        "user_info": None,
        "last_updated": created_at
    }
    
    # 实际应用中，这里应该生成真实的二维码图片
    # 为了演示，我们返回一个模拟的二维码URL
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://ai-agriculture-platform.com/auth/qr/callback/{qr_id}"
    
    return QRLoginResponse(
        qr_id=qr_id,
        qr_code_url=qr_code_url,
        expires_in=expires_in,
        created_at=created_at.isoformat()
    )

@auth_router.get("/qr/status/{qr_id}", response_model=QRLoginStatusResponse, status_code=status.HTTP_200_OK)
def check_qr_status(qr_id: str):
    """
    检查扫码登录状态
    前端轮询此接口以获取登录状态
    """
    # 检查会话是否存在
    if qr_id not in qr_login_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="二维码不存在"
        )
    
    session = qr_login_sessions[qr_id]
    
    # 检查是否过期
    if datetime.now() > session["expires_at"]:
        session["status"] = "expired"
        
    return QRLoginStatusResponse(
        qr_id=qr_id,
        status=session["status"],
        user_info=session["user_info"],
        access_token=session.get("access_token")
    )

@auth_router.post("/qr/callback", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def qr_callback(request: QRCallbackRequest):
    """
    扫码回调接口
    由第三方平台（微信、支付宝）调用，通知扫码状态
    """
    qr_id = request.qr_id
    user_id = request.user_id
    source = request.source
    action = request.action
    
    # 检查会话是否存在
    if qr_id not in qr_login_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="二维码不存在"
        )
    
    session = qr_login_sessions[qr_id]
    
    # 检查是否过期
    if datetime.now() > session["expires_at"]:
        session["status"] = "expired"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="二维码已过期"
        )
    
    # 处理不同的操作
    if action == "scan":
        # 用户已扫码，等待确认
        session["status"] = "scanned"
        session["last_updated"] = datetime.now()
        
    elif action == "confirm":
        # 用户已确认登录
        session["status"] = "confirmed"
        session["last_updated"] = datetime.now()
        
        # 模拟获取用户信息
        # 实际应用中，这里应该从第三方平台获取真实的用户信息
        user_info = users_db.get(user_id)
        if not user_info:
            # 如果是新用户，创建新用户记录
            user_info = {
                "id": user_id,
                "username": f"{source}_{user_id[:8]}",
                "avatar": f"https://example.com/{source}_avatar.jpg",
                "source": source,
                "created_at": datetime.now().isoformat()
            }
            users_db[user_id] = user_info
        
        session["user_info"] = user_info
        
        # 生成访问令牌
        # 实际应用中，这里应该生成JWT令牌
        access_token = str(uuid.uuid4())
        session["access_token"] = access_token
        
    elif action == "cancel":
        # 用户取消登录
        session["status"] = "cancelled"
        session["last_updated"] = datetime.now()
    
    return {
        "message": "操作成功",
        "qr_id": qr_id,
        "status": session["status"]
    }

@auth_router.post("/register/code", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def register_with_code(request: CodeRegistrationRequest):
    """
    使用产品注册码注册账号
    """
    code = request.code
    email = request.email
    password = request.password

    # 检查注册码是否存在且未使用
    if code not in product_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的注册码"
        )
    if product_codes[code]["status"] == "used":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注册码已被使用"
        )

    # 检查邮箱是否已注册
    for user_id, user_info in users_db.items():
        if user_info.get("email") == email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已被注册"
            )

    # 创建新用户
    new_user_id = str(uuid.uuid4())
    new_user = {
        "id": new_user_id,
        "username": email.split("@")[0],
        "email": email,
        "password": password,
        "avatar": "https://example.com/default_avatar.jpg",
        "source": "local",
        "role": product_codes[code]["type"],
        "created_at": datetime.now().isoformat()
    }
    users_db[new_user_id] = new_user

    # 标记注册码为已使用
    product_codes[code]["status"] = "used"
    product_codes[code]["used_by"] = new_user_id

    # 生成访问令牌
    access_token = str(uuid.uuid4())

    return {
        "message": "注册成功",
        "user_info": {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "avatar": new_user["avatar"],
            "source": new_user["source"],
            "role": new_user["role"]
        },
        "access_token": access_token,
        "token_type": "bearer"
    }

@auth_router.post("/logout", response_model=Dict[str, str], status_code=status.HTTP_200_OK)
def logout():
    """
    用户登出
    """
    # 实际应用中，这里应该失效用户的访问令牌
    return {"message": "登出成功"}

@auth_router.post("/login", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def password_login(request: PasswordLoginRequest):
    """
    密码登录接口
    """
    # 查找用户
    user = None
    for user_id, user_info in users_db.items():
        if user_info.get("email") == request.email:
            user = user_info
            break
    
    # 验证用户和密码
    if not user or user.get("password") != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )
    
    # 生成访问令牌
    access_token = str(uuid.uuid4())
    
    # 构建返回的用户信息，不包含密码
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "email": user.get("email"),
        "avatar": user["avatar"],
        "source": user["source"],
        "role": user.get("role", "user")
    }
    
    return {
        "message": "登录成功",
        "user_info": user_info,
        "access_token": access_token,
        "token_type": "bearer"
    }

@auth_router.get("/me", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_current_user():
    """
    获取当前用户信息
    """
    # 实际应用中，这里应该从请求头的Authorization获取令牌并验证
    # 为了演示，我们返回一个默认用户
    return {
        "id": "test_user",
        "username": "测试用户",
        "email": "test@example.com",
        "avatar": "https://example.com/test_avatar.jpg",
        "source": "local",
        "role": "admin"
    }

# --------------------------
# 社区相关代码
# --------------------------
community_router = APIRouter(prefix="/api/community", tags=["community"])

# 模拟直播流数据
live_streams_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "小麦种植技术分享",
        "streamer": "农业专家李明",
        "category": "种植技术",
        "viewers": 1234,
        "status": "live",
        "cover_image": "https://via.placeholder.com/640x360/1f2937/ffffff?text=Live+Stream+1",
        "tags": ["小麦", "种植", "技术"],
        "start_time": datetime.now().isoformat(),
        "streamer_avatar": "https://example.com/avatar_li.jpg",
        "description": "分享小麦种植的最新技术和管理方法"
    },
    {
        "id": 2,
        "title": "果园病虫害防治",
        "streamer": "植保专家王芳",
        "category": "病虫害防治",
        "viewers": 567,
        "status": "upcoming",
        "cover_image": "https://via.placeholder.com/640x360/1f2937/ffffff?text=Live+Stream+2",
        "tags": ["果树", "病虫害", "防治"],
        "start_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "streamer_avatar": "https://example.com/avatar_wang.jpg",
        "description": "讲解果园常见病虫害的识别和防治技术"
    },
    {
        "id": 3,
        "title": "农产品电商运营",
        "streamer": "电商导师赵强",
        "category": "农产品销售",
        "viewers": 890,
        "status": "live",
        "cover_image": "https://via.placeholder.com/640x360/1f2937/ffffff?text=Live+Stream+3",
        "tags": ["电商", "销售", "农产品"],
        "start_time": datetime.now().isoformat(),
        "streamer_avatar": "https://example.com/avatar_zhao.jpg",
        "description": "分享农产品电商平台的运营策略和技巧"
    }
]

# 模拟社区帖子数据
community_posts_db: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "分享一个提高产量的小技巧",
        "content": "我在种植过程中发现，合理使用有机肥可以显著提高作物产量，同时减少病虫害的发生。",
        "user_id": "user_123",
        "username": "农民张",
        "avatar": "https://example.com/avatar_zhang.jpg",
        "likes": 45,
        "comments": [
            {
                "id": 1,
                "user_id": "user_456",
                "username": "农业爱好者",
                "content": "谢谢分享，我也试试！",
                "time": "2小时前",
                "likes": 5
            },
            {
                "id": 2,
                "user_id": "user_789",
                "username": "农技推广员",
                "content": "这个方法确实有效，我们也在推广。",
                "time": "1小时前",
                "likes": 3
            }
        ],
        "time": "3小时前",
        "tags": ["种植技巧", "有机肥"],
        "category": "种植经验"
    },
    {
        "id": 2,
        "title": "求助：果树叶子发黄怎么办？",
        "content": "我的苹果树最近叶子开始发黄，不知道是什么原因，有谁能帮忙分析一下吗？",
        "user_id": "user_456",
        "username": "果园主小李",
        "avatar": "https://example.com/avatar_li_orchard.jpg",
        "likes": 23,
        "comments": [
            {
                "id": 3,
                "user_id": "user_101",
                "username": "植保专家",
                "content": "可能是缺铁性黄叶病，建议补充铁元素肥料。",
                "time": "45分钟前",
                "likes": 12
            }
        ],
        "time": "1小时前",
        "tags": ["果树", "病虫害", "求助"],
        "category": "病虫害防治"
    },
    {
        "id": 3,
        "title": "新型农业机械使用体验",
        "content": "最近购买了一台新型播种机，效率提高了50%，而且省种子，非常好用！",
        "user_id": "user_789",
        "username": "农机达人",
        "avatar": "https://example.com/avatar_machine.jpg",
        "likes": 67,
        "comments": [],
        "time": "5小时前",
        "tags": ["农业机械", "播种机", "使用体验"],
        "category": "农业机械"
    }
]

class CommentCreateRequest(BaseModel):
    """创建评论请求模型"""
    content: str

class LikePostRequest(BaseModel):
    """点赞帖子请求模型"""
    post_id: int

class LikeCommentRequest(BaseModel):
    """点赞评论请求模型"""
    post_id: int
    comment_id: int

@community_router.get("/live-streams", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
def get_live_streams():
    """
    获取直播流列表
    """
    return live_streams_db

@community_router.get("/live-streams/{stream_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_live_stream(stream_id: int):
    """
    获取单个直播流详情
    """
    for stream in live_streams_db:
        if stream["id"] == stream_id:
            return stream
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="直播流不存在"
    )

class LiveStreamCommentRequest(BaseModel):
    """直播流评论请求模型"""
    content: str

@community_router.post("/live-streams/{stream_id}/comments", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_live_stream_comment(stream_id: int, request: LiveStreamCommentRequest):
    """
    在直播流中发表评论
    """
    # 检查直播流是否存在
    stream = None
    for s in live_streams_db:
        if s["id"] == stream_id:
            stream = s
            break

    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="直播流不存在"
        )

    new_comment = {
        "id": int(datetime.now().timestamp() * 1000),
        "user_id": "current_user",
        "username": "当前用户",
        "content": request.content,
        "time": "刚刚",
        "likes": 0
    }
    return new_comment


def get_community_posts(category: Optional[str] = None, search: Optional[str] = None):
    """
    获取社区帖子列表
    """
    posts = community_posts_db
    
    # 按分类过滤
    if category:
        posts = [post for post in posts if post["category"] == category]
    
    # 按关键词搜索
    if search:
        search_lower = search.lower()
        posts = [
            post for post in posts 
            if search_lower in post["title"].lower() 
            or search_lower in post["content"].lower()
            or any(tag.lower().find(search_lower) != -1 for tag in post["tags"])
        ]
    
    return posts

@community_router.get("/posts/{post_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_community_post(post_id: int):
    """
    获取单个社区帖子详情
    """
    for post in community_posts_db:
        if post["id"] == post_id:
            return post
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="帖子不存在"
    )

@community_router.post("/posts/{post_id}/comments", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, request: CommentCreateRequest):
    """
    创建评论
    """
    # 查找帖子
    post = None
    for p in community_posts_db:
        if p["id"] == post_id:
            post = p
            break
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )
    
    # 创建新评论
    new_comment = {
        "id": len(post["comments"]) + 1,
        "user_id": "current_user",  # 实际应用中应该从请求中获取当前用户ID
        "username": "当前用户",  # 实际应用中应该从请求中获取当前用户名
        "content": request.content,
        "time": "刚刚",
        "likes": 0
    }
    
    # 添加到帖子的评论列表
    post["comments"].append(new_comment)
    
    return new_comment

@community_router.post("/posts/{post_id}/like", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def like_post(post_id: int):
    """
    点赞帖子
    """
    # 查找帖子
    post = None
    for p in community_posts_db:
        if p["id"] == post_id:
            post = p
            break
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )
    
    # 增加点赞数
    post["likes"] += 1
    
    return {"likes": post["likes"]}

@community_router.post("/posts/{post_id}/comments/{comment_id}/like", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def like_comment(post_id: int, comment_id: int):
    """
    点赞评论
    """
    # 查找帖子
    post = None
    for p in community_posts_db:
        if p["id"] == post_id:
            post = p
            break
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="帖子不存在"
        )
    
    # 查找评论
    comment = None
    for c in post["comments"]:
        if c["id"] == comment_id:
            comment = c
            break
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在"
        )
    
    # 增加点赞数
    comment["likes"] += 1
    
    return {"likes": comment["likes"]}

@community_router.get("/categories", response_model=List[str], status_code=status.HTTP_200_OK)
def get_categories():
    """
    获取所有帖子分类
    """
    categories = set()
    for post in community_posts_db:
        categories.add(post["category"])
    return list(categories)

@community_router.post("/live-streams/{stream_id}/comments", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_live_stream_comment(stream_id: int, request: CommentCreateRequest):
    """
    提交直播间评论
    """
    for stream in live_streams_db:
        if stream["id"] == stream_id:
            comment = {
                "id": str(uuid.uuid4()),
                "stream_id": stream_id,
                "content": request.content,
                "username": "当前用户",
                "created_at": datetime.now().isoformat()
            }
            return {"success": True, "data": comment}
    raise HTTPException(status_code=404, detail="直播流不存在")

# --------------------------
# 系统API路由
# --------------------------
system_router = APIRouter(prefix="/api/system", tags=["system"])

@system_router.get("/metrics")
async def get_system_metrics():
    """获取系统指标"""
    return {
        "success": True,
        "data": {
            "cpu_usage": 45.2,
            "memory_usage": 62.8,
            "disk_usage": 38.5,
            "network_in": 1024,
            "network_out": 2048,
            "active_connections": 12,
            "uptime": "3d 5h 20m"
        }
    }

@system_router.get("/health")
async def get_system_health():
    """获取系统健康状态"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "services": {
                "database": "up",
                "cache": "up",
                "ai_service": "up",
                "storage": "up"
            },
            "last_check": datetime.now().isoformat()
        }
    }

@system_router.get("/logs")
async def get_system_logs(limit: int = 100):
    """获取系统日志"""
    logs = [
        {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "系统启动成功"},
        {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "AI模型加载完成"},
        {"timestamp": datetime.now().isoformat(), "level": "WARN", "message": "网络延迟较高"},
        {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "数据同步完成"},
    ]
    return {
        "success": True,
        "data": logs[:limit]
    }

@system_router.post("/settings")
async def update_system_settings(settings: Dict[str, Any]):
    """更新系统设置"""
    return {
        "success": True,
        "data": {"message": "设置已更新", "settings": settings}
    }

# --------------------------
# 摄像头API路由
# --------------------------
camera_router = APIRouter(prefix="/api/camera", tags=["camera"])

# ── 摄像头控制器：优先使用 CameraController（真实 cv2），否则降级为纯内存模拟 ──
if _CameraController is not None:
    _camera_ctrl = _CameraController()
    _USE_REAL_CTRL = True
else:
    _camera_ctrl = None
    _USE_REAL_CTRL = False

# ── PTZ 云台控制器（全局单例，用于保持连接状态）──────────────────────────────
_ptz_ctrl = None  # PTZCameraController 实例，连接后设置
_ptz_auto_tracking = False  # 是否启用自动跟踪
_ptz_simulated_connected = False  # 模拟模式下的连接标志
_ptz_simulated_position = {"pan": 0.0, "tilt": 0.0, "zoom": 1.0}  # 模拟位置

# 弹球式模拟目标速度（像素/帧），初始随机方向
_sim_target_vel = [4, 3]   # [vx, vy]，正负表示方向


def _get_ptz_status_dict() -> dict:
    """返回统一格式的 PTZ 状态字典"""
    # 真实控制器
    if _ptz_ctrl is not None:
        s = _ptz_ctrl.get_status()
        s["auto_tracking"] = _ptz_auto_tracking
        return s
    # 模拟模式已连接
    if _ptz_simulated_connected:
        return {
            "connected": True,
            "protocol": "simulated",
            "connection_type": "simulated",
            "position": dict(_ptz_simulated_position),
            "presets": {},
            "auto_tracking": _ptz_auto_tracking,
            "simulated": True,
        }
    # 未连接
    return {
        "connected": False,
        "protocol": None,
        "connection_type": None,
        "position": {"pan": 0.0, "tilt": 0.0, "zoom": 1.0},
        "presets": {},
        "auto_tracking": False,
    }

# 降级用的内存状态（仅当 CameraController 不可用时使用）
camera_state = {
    "is_open": False,
    "camera_index": 0,
    "tracking_active": False,
    "recognition_active": False
}


def _ctrl_is_open() -> bool:
    if _USE_REAL_CTRL:
        return _camera_ctrl.is_camera_open()
    return camera_state["is_open"]


def _ctrl_open(index: int = 0) -> dict:
    if _USE_REAL_CTRL:
        return _camera_ctrl.open_camera(index)
    camera_state["is_open"] = True
    camera_state["camera_index"] = index
    return {"success": True, "message": "摄像头已打开（模拟）", "camera_index": index,
            "camera_info": {"type": "simulated", "width": 640, "height": 480, "fps": 30}}


def _ctrl_close() -> dict:
    if _USE_REAL_CTRL:
        return _camera_ctrl.close_camera()
    camera_state["is_open"] = False
    camera_state["tracking_active"] = False
    camera_state["recognition_active"] = False
    return {"success": True, "message": "摄像头已关闭"}


def _ctrl_get_frame_jpeg() -> Optional[bytes]:
    """获取当前帧并返回 JPEG bytes；失败返回 None。"""
    if _USE_REAL_CTRL and _CV2_AVAILABLE:
        frame = _camera_ctrl.get_current_frame()
        if frame is not None:
            ok, buf = _cv2.imencode('.jpg', frame, [_cv2.IMWRITE_JPEG_QUALITY, 80])
            if ok:
                return bytes(buf)
    return None


@camera_router.post("/open")
async def open_camera(request: Dict[str, Any]):
    """打开摄像头（优先真实设备，失败自动降级模拟）"""
    index = request.get("camera_index", 0)
    result = _ctrl_open(index)
    return {"success": result.get("success", False), "data": result}


@camera_router.post("/close")
async def close_camera():
    """关闭摄像头"""
    result = _ctrl_close()
    return {"success": result.get("success", False), "data": result}


@camera_router.get("/status")
async def get_camera_status():
    """获取摄像头状态"""
    is_open = _ctrl_is_open()
    cam_index = _camera_ctrl.camera_index if _USE_REAL_CTRL else camera_state["camera_index"]
    cam_type = ("real" if (_USE_REAL_CTRL and is_open and getattr(_camera_ctrl, 'camera_index', 999) != 999)
                else "simulated")
    return {
        "success": True,
        "data": {
            "is_open": is_open,
            "camera_index": cam_index,
            "tracking_active": (camera_state["tracking_active"] if not _USE_REAL_CTRL
                                 else getattr(_camera_ctrl, 'tracking_enabled', False)),
            "recognition_active": (camera_state["recognition_active"] if not _USE_REAL_CTRL
                                    else getattr(_camera_ctrl, 'recognizing_enabled', False)),
            "camera_type": cam_type,
            "controller": "real" if _USE_REAL_CTRL else "simulated"
        }
    }


@camera_router.get("/list")
async def list_cameras():
    """列出可用摄像头"""
    if _USE_REAL_CTRL:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: _camera_ctrl.list_cameras(3, 0.5))
        return {"success": True, "data": result}
    return {
        "success": True,
        "data": {
            "cameras": [{"index": 999, "type": "simulated", "width": 640, "height": 480, "fps": 30}]
        }
    }


@camera_router.get("/frame")
async def get_camera_frame():
    """获取单帧（HTTP 方式，WebSocket 更实时）"""
    if not _ctrl_is_open():
        raise HTTPException(status_code=400, detail="摄像头未打开")
    loop = asyncio.get_event_loop()
    jpeg = await loop.run_in_executor(None, _ctrl_get_frame_jpeg)
    if jpeg:
        return {
            "success": True,
            "data": {
                "frame_base64": base64.b64encode(jpeg).decode(),
                "format": "jpeg",
                "timestamp": datetime.now().isoformat()
            }
        }
    return {"success": False, "data": {"message": "暂无帧数据"}}


@camera_router.post("/tracking/start")
async def start_tracking(request: Dict[str, Any]):
    """开始目标跟踪"""
    if _USE_REAL_CTRL:
        result = _camera_ctrl.start_visual_tracking(request.get("tracker_type", "CSRT"))
        return {"success": result.get("success", False), "data": result}
    camera_state["tracking_active"] = True
    return {"success": True, "data": {"message": "目标跟踪已启动", "target": request.get("target", "default")}}


@camera_router.post("/tracking/stop")
async def stop_tracking():
    """停止目标跟踪"""
    if _USE_REAL_CTRL:
        result = _camera_ctrl.stop_visual_tracking()
        return {"success": result.get("success", False), "data": result}
    camera_state["tracking_active"] = False
    return {"success": True, "data": {"message": "目标跟踪已停止"}}


@camera_router.post("/recognition/start")
async def start_recognition(request: Dict[str, Any]):
    """开始图像识别"""
    if _USE_REAL_CTRL:
        result = _camera_ctrl.start_visual_recognition(request.get("model", "haar"))
        return {"success": result.get("success", False), "data": result}
    camera_state["recognition_active"] = True
    return {"success": True, "data": {"message": "图像识别已启动", "model": request.get("model", "default")}}


@camera_router.post("/recognition/stop")
async def stop_recognition():
    """停止图像识别"""
    if _USE_REAL_CTRL:
        result = _camera_ctrl.stop_visual_recognition()
        return {"success": result.get("success", False), "data": result}
    camera_state["recognition_active"] = False
    return {"success": True, "data": {"message": "图像识别已停止"}}


@camera_router.get("/tracking/status")
async def get_tracking_status():
    """获取跟踪状态"""
    if _USE_REAL_CTRL:
        s = _camera_ctrl.get_tracking_status()
        return {"success": True, "data": s}
    return {
        "success": True,
        "data": {
            "tracking_enabled": camera_state["tracking_active"],
            "tracker_type": "kcf" if camera_state["tracking_active"] else None
        }
    }


@camera_router.get("/recognition/status")
async def get_recognition_status():
    """获取识别状态"""
    if _USE_REAL_CTRL:
        s = _camera_ctrl.get_recognition_status()
        return {"success": True, "data": s}
    return {
        "success": True,
        "data": {
            "recognizing_enabled": camera_state["recognition_active"],
            "recognized_objects_count": 5 if camera_state["recognition_active"] else 0
        }
    }


# ── 生成模拟摄像头帧（降级备用，无需 Pillow/OpenCV）──────────────────────────
def _make_png_frame(width: int = 320, height: int = 180, tick: int = 0) -> bytes:
    """生成一帧带时间戳纹理的彩色 PNG（纯标准库实现）"""
    def _pack_chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    # 构建像素数据（RGB 扫描行，带滤波字节 0x00）
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)  # 无滤波
        for x in range(width):
            r = int((x / width) * 200 + 55) & 0xFF
            g = int((y / height) * 200 + 55) & 0xFF
            b = int(((x + y + tick * 4) % 256))
            raw_rows += bytes([r, g, b])
    idat_data = zlib.compress(bytes(raw_rows), 6)

    return (
        b'\x89PNG\r\n\x1a\n'
        + _pack_chunk(b'IHDR', ihdr_data)
        + _pack_chunk(b'IDAT', idat_data)
        + _pack_chunk(b'IEND', b'')
    )


@camera_router.websocket("/ws/frame")
async def camera_ws_frame(websocket: WebSocket):
    """
    WebSocket 推送摄像头帧。
    优先顺序：① CameraController 真实帧（JPEG）→ ② 降级模拟 PNG
    """
    await websocket.accept()
    tick = 0
    loop = asyncio.get_event_loop()
    try:
        while True:
            if not _ctrl_is_open():
                await websocket.send_json({"success": False, "message": "摄像头未打开"})
                await asyncio.sleep(0.5)
                continue

            # 尝试从真实控制器获取帧
            jpeg_bytes = None
            if _USE_REAL_CTRL:
                jpeg_bytes = await loop.run_in_executor(None, _ctrl_get_frame_jpeg)

            if jpeg_bytes:
                frame_b64 = base64.b64encode(jpeg_bytes).decode()
                await websocket.send_json({
                    "success": True,
                    "frame_base64": frame_b64,
                    "format": "jpeg",
                    "source": "real",
                    "timestamp": datetime.now().isoformat(),
                })
            else:
                # 降级：生成模拟 PNG 帧
                png_bytes = _make_png_frame(tick=tick)
                frame_b64 = base64.b64encode(png_bytes).decode()
                await websocket.send_json({
                    "success": True,
                    "frame_base64": frame_b64,
                    "format": "png",
                    "source": "simulated",
                    "timestamp": datetime.now().isoformat(),
                    "tick": tick,
                })

            tick = (tick + 1) % 256
            await asyncio.sleep(0.1)  # 10fps，降低 CPU 占用

    except WebSocketDisconnect:
        pass
    except Exception:
        pass




@camera_router.get("/ptz/status")
async def get_ptz_status():
    """获取云台状态"""
    return {"success": True, "data": _get_ptz_status_dict()}


@camera_router.post("/ptz/connect")
async def connect_ptz(params: Dict[str, Any]):
    """连接云台"""
    global _ptz_ctrl, _ptz_simulated_connected
    if _PTZCameraController is None:
        # 没有真实控制器，进入软件模拟模式
        _ptz_simulated_connected = True
        return {
            "success": True,
            "data": {"message": "云台已连接（模拟模式）", "simulated": True}
        }
    try:
        protocol_str = params.get("protocol", "pelco_d")
        connection_type = params.get("connection_type", "serial")
        # 协议枚举映射
        proto_map = {
            "pelco_d": _PTZProtocol.PELCO_D,
            "pelco_p": _PTZProtocol.PELCO_P,
            "visca":   _PTZProtocol.VISCA,
            "onvif":   _PTZProtocol.ONVIF,
            "http":    _PTZProtocol.HTTP_API,
        }
        protocol = proto_map.get(protocol_str, _PTZProtocol.PELCO_D)
        # 收集连接参数
        conn_kwargs: Dict[str, Any] = {}
        if connection_type == "serial":
            conn_kwargs["port"]     = params.get("port", "/dev/ttyUSB0")
            conn_kwargs["baudrate"] = params.get("baudrate", 9600)
            conn_kwargs["address"]  = params.get("address", 1)
        elif connection_type == "network":
            conn_kwargs["host"]         = params.get("host", "192.168.1.100")
            conn_kwargs["port"]         = params.get("network_port", 5000)
            conn_kwargs["address"]      = params.get("address", 1)
        elif connection_type == "http":
            conn_kwargs["base_url"]  = params.get("base_url", "http://192.168.1.100")
            conn_kwargs["username"]  = params.get("username", "admin")
            conn_kwargs["password"]  = params.get("password", "admin")

        _ptz_ctrl = _PTZCameraController(
            protocol=protocol,
            connection_type=connection_type,
            **conn_kwargs
        )
        result = await _ptz_ctrl.connect()
        if not result.get("success"):
            # 真实硬件连接失败 → 降级为软件模拟
            _ptz_ctrl = None
            _ptz_simulated_connected = True
            return {
                "success": True,
                "data": {
                    "message": f"硬件连接失败（{result.get('message', '未知错误')}），已切换至模拟模式",
                    "simulated": True,
                    "hardware_error": result.get("message"),
                }
            }
        return {"success": True, "data": result}
    except Exception as e:
        # 异常也降级
        _ptz_ctrl = None
        _ptz_simulated_connected = True
        return {
            "success": True,
            "data": {
                "message": f"硬件异常（{str(e)}），已切换至模拟模式",
                "simulated": True,
                "hardware_error": str(e),
            }
        }


@camera_router.post("/ptz/disconnect")
async def disconnect_ptz():
    """断开云台"""
    global _ptz_ctrl, _ptz_auto_tracking, _ptz_simulated_connected
    _ptz_auto_tracking = False
    _ptz_simulated_connected = False
    if _ptz_ctrl is None:
        return {"success": True, "data": {"message": "云台未连接"}}
    try:
        result = await _ptz_ctrl.disconnect()
        _ptz_ctrl = None
        return {"success": result.get("success", True), "data": result}
    except Exception as e:
        _ptz_ctrl = None
        return {"success": False, "data": {"message": f"断开失败: {str(e)}"}}


@camera_router.post("/ptz/action")
async def ptz_action(params: Dict[str, Any]):
    """云台方向/变焦动作"""
    global _ptz_ctrl, _ptz_simulated_position
    action_str = params.get("action", "stop")
    speed = int(params.get("speed", 50))
    preset_id = params.get("preset_id", 1)

    # 没有真实控制器时使用软件模拟（纯内存，只更新前端状态）
    if _ptz_ctrl is None or _PTZAction is None:
        # 软件模拟位置更新
        spd = speed / 100.0
        if action_str == "pan_left":
            _ptz_simulated_position["pan"] = max(-180, _ptz_simulated_position["pan"] - 5 * spd)
        elif action_str == "pan_right":
            _ptz_simulated_position["pan"] = min(180, _ptz_simulated_position["pan"] + 5 * spd)
        elif action_str == "tilt_up":
            _ptz_simulated_position["tilt"] = min(90, _ptz_simulated_position["tilt"] + 3 * spd)
        elif action_str == "tilt_down":
            _ptz_simulated_position["tilt"] = max(-90, _ptz_simulated_position["tilt"] - 3 * spd)
        elif action_str == "zoom_in":
            _ptz_simulated_position["zoom"] = min(20.0, _ptz_simulated_position["zoom"] + 0.5 * spd)
        elif action_str == "zoom_out":
            _ptz_simulated_position["zoom"] = max(1.0, _ptz_simulated_position["zoom"] - 0.5 * spd)
        return {
            "success": True,
            "data": {
                "message": f"云台执行动作（模拟）: {action_str}",
                "simulated": True,
                "position": dict(_ptz_simulated_position),
            }
        }
    try:
        action_map = {
            "pan_left":    _PTZAction.PAN_LEFT,
            "pan_right":   _PTZAction.PAN_RIGHT,
            "tilt_up":     _PTZAction.TILT_UP,
            "tilt_down":   _PTZAction.TILT_DOWN,
            "zoom_in":     _PTZAction.ZOOM_IN,
            "zoom_out":    _PTZAction.ZOOM_OUT,
            "focus_near":  _PTZAction.FOCUS_NEAR,
            "focus_far":   _PTZAction.FOCUS_FAR,
            "iris_open":   _PTZAction.IRIS_OPEN,
            "iris_close":  _PTZAction.IRIS_CLOSE,
            "preset_set":  _PTZAction.PRESET_SET,
            "preset_goto": _PTZAction.PRESET_GOTO,
            "auto_scan":   _PTZAction.AUTO_SCAN,
            "patrol":      _PTZAction.PATROL,
            "stop":        _PTZAction.STOP,
        }
        action = action_map.get(action_str)
        if action is None:
            return {"success": False, "data": {"message": f"未知动作: {action_str}"}}

        extra = {}
        if action_str in ("preset_set", "preset_goto"):
            extra["preset_id"] = preset_id

        result = await _ptz_ctrl.execute_action(action, speed, **extra)
        # 附带最新位置
        result["position"] = {
            "pan":  _ptz_ctrl.current_pan,
            "tilt": _ptz_ctrl.current_tilt,
            "zoom": _ptz_ctrl.current_zoom,
        }
        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        return {"success": False, "data": {"message": f"执行失败: {str(e)}"}}


@camera_router.post("/ptz/move")
async def ptz_move(params: Dict[str, Any]):
    """云台绝对位置移动"""
    global _ptz_simulated_position
    if _ptz_ctrl is None:
        # 模拟模式：直接更新内存位置
        _ptz_simulated_position["pan"]  = float(params.get("pan", 0))
        _ptz_simulated_position["tilt"] = float(params.get("tilt", 0))
        _ptz_simulated_position["zoom"] = float(params.get("zoom", 1.0))
        return {
            "success": True,
            "data": {
                "message": "云台移动完成（模拟）",
                "current_position": dict(_ptz_simulated_position),
                "simulated": True,
            }
        }
    try:
        result = await _ptz_ctrl.move_to_position(
            pan=float(params.get("pan", 0)),
            tilt=float(params.get("tilt", 0)),
            zoom=params.get("zoom"),
            speed=int(params.get("speed", 50)),
        )
        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        return {"success": False, "data": {"message": f"移动失败: {str(e)}"}}


@camera_router.post("/ptz/preset/set")
async def set_ptz_preset(params: Dict[str, Any]):
    """设置预置位"""
    if _ptz_ctrl is None:
        return {"success": True, "data": {"message": f"预置位 {params.get('preset_id')} 已设置（模拟）"}}
    try:
        result = await _ptz_ctrl.set_preset(
            preset_id=int(params.get("preset_id", 1)),
            name=params.get("name"),
        )
        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        return {"success": False, "data": {"message": f"设置失败: {str(e)}"}}


@camera_router.post("/ptz/preset/goto")
async def goto_ptz_preset(params: Dict[str, Any]):
    """跳转到预置位"""
    if _ptz_ctrl is None:
        return {"success": True, "data": {"message": f"已跳转预置位（模拟）"}}
    try:
        result = await _ptz_ctrl.goto_preset(preset_id=int(params.get("preset_id", 1)))
        return {"success": result.get("success", False), "data": result}
    except Exception as e:
        return {"success": False, "data": {"message": f"跳转失败: {str(e)}"}}


# ── PTZ 自动跟踪后台任务 ─────────────────────────────────────────────────────
_ptz_track_task: Optional[asyncio.Task] = None  # 跟踪后台任务句柄
_ptz_track_status: dict = {                      # 跟踪运行时状态（供前端查询）
    "running": False,
    "target_found": False,
    "target_bbox": None,       # (x, y, w, h)
    "frame_size": None,        # (w, h)
    "pan_offset": 0.0,
    "tilt_offset": 0.0,
    "last_adjust": None,       # ISO时间字符串
    "tracker_type": "CSRT",
    "mode": "simulated",       # "real" | "simulated"
    "error": None,
}


async def _ptz_auto_track_loop():
    """
    PTZ 自动跟踪后台协程：
      1. 从 CameraController 获取当前帧
      2. 用已启动的视觉跟踪器取目标 bbox
      3. 调用 PTZCameraController.auto_track_object 驱动云台
      4. 无真实摄像头时走纯模拟（随机目标偏移）
    """
    global _ptz_auto_tracking, _ptz_track_status, _ptz_simulated_position

    import random

    _ptz_track_status["running"] = True
    _ptz_track_status["error"] = None

    try:
        while _ptz_auto_tracking:
            await asyncio.sleep(0.25)  # ~4 fps

            # ── 模式1：真实控制器 + 真实摄像头 ──────────────────────────
            if _ptz_ctrl is not None and _USE_REAL_CTRL and _ctrl_is_open():
                loop = asyncio.get_event_loop()
                frame = await loop.run_in_executor(None, _camera_ctrl.get_current_frame)
                if frame is None:
                    _ptz_track_status["target_found"] = False
                    continue

                frame_h, frame_w = frame.shape[:2]
                _ptz_track_status["frame_size"] = (frame_w, frame_h)
                _ptz_track_status["mode"] = "real"

                # 取最新 tracking 结果（由 CameraController 后台线程持续更新）
                ts = _camera_ctrl.get_tracking_status()
                bbox = ts.get("tracked_object")
                if bbox is None:
                    # 尝试识别结果
                    rs = _camera_ctrl.get_recognition_status()
                    objs = rs.get("recognized_objects", [])
                    if objs:
                        bbox = objs[0].get("bbox")

                if bbox is None:
                    _ptz_track_status["target_found"] = False
                    continue

                _ptz_track_status["target_found"] = True
                _ptz_track_status["target_bbox"] = list(bbox)

                # 调用云台跟踪
                result = await _ptz_ctrl.auto_track_object(bbox, (frame_w, frame_h))
                if result.get("success"):
                    off = result.get("offset", {})
                    _ptz_track_status["pan_offset"] = round(off.get("pan", 0), 2)
                    _ptz_track_status["tilt_offset"] = round(off.get("tilt", 0), 2)
                    _ptz_track_status["last_adjust"] = datetime.now().isoformat()
                continue

            # ── 模式2：模拟云台（纯软件弹球式）──────────────────────────
            _ptz_track_status["mode"] = "simulated"
            frame_w, frame_h = 640, 480
            bw, bh = 80, 80  # 目标框大小固定

            # 初始化目标
            if not _ptz_track_status["target_found"] or _ptz_track_status["target_bbox"] is None:
                _ptz_track_status["target_bbox"] = [
                    frame_w // 2 - bw // 2,
                    frame_h // 2 - bh // 2,
                    bw, bh,
                ]
                _ptz_track_status["target_found"] = True
                _sim_target_vel[0] = random.choice([-5, -4, 4, 5])
                _sim_target_vel[1] = random.choice([-3, -2, 2, 3])

            bx, by = _ptz_track_status["target_bbox"][0], _ptz_track_status["target_bbox"][1]

            # 弹球运动：碰边界反向
            bx += _sim_target_vel[0]
            by += _sim_target_vel[1]
            if bx <= 0 or bx >= frame_w - bw:
                _sim_target_vel[0] = -_sim_target_vel[0]
                bx = max(0, min(frame_w - bw, bx))
            if by <= 0 or by >= frame_h - bh:
                _sim_target_vel[1] = -_sim_target_vel[1]
                by = max(0, min(frame_h - bh, by))

            _ptz_track_status["target_bbox"] = [bx, by, bw, bh]
            _ptz_track_status["frame_size"] = (frame_w, frame_h)

            # 计算目标中心相对画面中心的偏移（角度）
            cx = bx + bw / 2
            cy = by + bh / 2
            pan_offset = (cx - frame_w / 2) / frame_w * 30   # 最大 ±15°
            tilt_offset = -(cy - frame_h / 2) / frame_h * 20  # 最大 ±10°

            _ptz_track_status["pan_offset"] = round(pan_offset, 2)
            _ptz_track_status["tilt_offset"] = round(tilt_offset, 2)

            # 云台跟踪：偏移超过阈值才调整，速度与偏移量成正比
            threshold = 3.0   # 降低阈值，更灵敏
            pan_speed = 0.6   # 每帧最大调整度数

            if abs(pan_offset) > threshold:
                delta = min(abs(pan_offset) * 0.08, pan_speed) * (1 if pan_offset > 0 else -1)
                _ptz_simulated_position["pan"] = max(-180, min(180,
                    _ptz_simulated_position["pan"] + delta))
            if abs(tilt_offset) > threshold:
                delta = min(abs(tilt_offset) * 0.08, pan_speed * 0.7) * (1 if tilt_offset > 0 else -1)
                _ptz_simulated_position["tilt"] = max(-90, min(90,
                    _ptz_simulated_position["tilt"] + delta))

            _ptz_track_status["last_adjust"] = datetime.now().isoformat()

    except asyncio.CancelledError:
        pass
    except Exception as e:
        _ptz_track_status["error"] = str(e)
    finally:
        _ptz_track_status["running"] = False
        _ptz_track_status["target_found"] = False


@camera_router.post("/ptz/auto-track/start")
async def start_ptz_auto_track():
    """开启云台自动跟踪"""
    global _ptz_auto_tracking, _ptz_track_task

    # 连接检查
    if _ptz_ctrl is None and not _ptz_simulated_connected:
        return {"success": False, "data": {"message": "请先连接云台"}}

    # 有真实控制器时需要摄像头
    if _ptz_ctrl is not None and not _ctrl_is_open():
        return {"success": False, "data": {"message": "请先开启摄像头"}}

    # 有真实摄像头 → 确保视觉跟踪器已启动
    if _USE_REAL_CTRL and _ctrl_is_open() and _camera_ctrl is not None:
        ts = _camera_ctrl.get_tracking_status()
        if not ts.get("tracking_enabled"):
            _camera_ctrl.start_visual_tracking("CSRT")
        _ptz_track_status["tracker_type"] = "CSRT"

    # 取消旧任务（如果有）
    if _ptz_track_task and not _ptz_track_task.done():
        _ptz_track_task.cancel()
        try:
            await _ptz_track_task
        except asyncio.CancelledError:
            pass

    _ptz_auto_tracking = True
    _ptz_track_task = asyncio.create_task(_ptz_auto_track_loop())

    mode = "real" if (_ptz_ctrl is not None and _USE_REAL_CTRL and _ctrl_is_open()) else "simulated"
    return {"success": True, "data": {
        "message": "自动跟踪已启动",
        "auto_tracking": True,
        "mode": mode,
    }}


@camera_router.post("/ptz/auto-track/stop")
async def stop_ptz_auto_track():
    """停止云台自动跟踪"""
    global _ptz_auto_tracking, _ptz_track_task
    _ptz_auto_tracking = False

    if _ptz_track_task and not _ptz_track_task.done():
        _ptz_track_task.cancel()
        try:
            await _ptz_track_task
        except asyncio.CancelledError:
            pass
        _ptz_track_task = None

    # 停止云台运动
    if _ptz_ctrl is not None and _PTZAction is not None:
        try:
            await _ptz_ctrl.execute_action(_PTZAction.STOP, 0)
        except Exception:
            pass

    # 停止视觉跟踪器
    if _USE_REAL_CTRL and _camera_ctrl is not None:
        try:
            _camera_ctrl.stop_visual_tracking()
        except Exception:
            pass

    _ptz_track_status["running"] = False
    _ptz_track_status["target_found"] = False
    return {"success": True, "data": {"message": "自动跟踪已停止", "auto_tracking": False}}


@camera_router.get("/ptz/auto-track/status")
async def get_ptz_auto_track_status():
    """获取自动跟踪实时状态（前端轮询）"""
    return {
        "success": True,
        "data": {
            **_ptz_track_status,
            "auto_tracking": _ptz_auto_tracking,
            "position": (
                {
                    "pan": _ptz_ctrl.current_pan,
                    "tilt": _ptz_ctrl.current_tilt,
                    "zoom": _ptz_ctrl.current_zoom,
                } if _ptz_ctrl is not None
                else dict(_ptz_simulated_position)
            ),
        }
    }

# --------------------------
# 模型API路由
# --------------------------
models_router = APIRouter(prefix="/api/models", tags=["models"])

# 模拟模型数据
models_db = [
    # ── 1. OrganicAICore 有机体进化决策核心 ──────────────────────────────
    {
        "id": "organic_core_v1",
        "name": "有机体进化决策核心",
        "description": "驱动 OrganicAICore 的自演化策略网络，基于 JAX/Flax 实现强化学习多步决策。"
                       "架构：MLP [256→512→256]，输入32维传感器状态，输出10类动作（调温/调湿/CO₂/光谱/资源分配等）。"
                       "推荐模型：PPO + SelfEvolvingPolicy（自研，无需外部API，本地运行）",
        "type": "reinforcement_learning",
        "status": "ready",
        "version": "4.2.0",
        "accuracy": 0.91,
        "size": 18 * 1024 * 1024,
        "agent": "OrganicAICore",
        "framework": "JAX/Flax",
        "recommended_model": "PPO-SelfEvolvingPolicy",
        "task": "农业环境多参数控制 / 区块链记录 / 资源调度",
        "input_dim": 32,
        "output_dim": 10,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 2. 农业视觉分类（ResNet50）──────────────────────────────────────
    {
        "id": "agriculture_resnet50_v1",
        "name": "农业作物视觉分类模型",
        "description": "ResNet50 骨干网络，224×224 RGB 输入，10类作物分类（已在 model_index 注册，acc=92%）。"
                       "用于 OrganicAICore 动作0（摄像头监控）触发的视觉感知子任务。"
                       "推荐模型：ResNet50（torchvision预训练权重，迁移学习微调）",
        "type": "vision",
        "status": "deployed",
        "version": "1.0.0",
        "accuracy": 0.92,
        "size": 98 * 1024 * 1024,
        "agent": "OrganicAICore / LearningAgent",
        "framework": "PyTorch",
        "recommended_model": "ResNet50",
        "task": "作物类型识别 / 病虫害图像检测",
        "input_dim": "224x224x3",
        "output_dim": 10,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 3. AdvancedAICore Transformer 策略网络 ───────────────────────────
    {
        "id": "advanced_transformer_v1",
        "name": "高级Transformer策略网络",
        "description": "AdvancedAICore 内嵌的 Transformer 决策头：d_model=256，4个注意力头，3层Encoder，"
                       "支持序列化状态输入，适合时序传感器数据的多步推理。"
                       "推荐模型：Time-Series Transformer（自研轻量版）或 PatchTST（开源可本地部署）",
        "type": "transformer",
        "status": "ready",
        "version": "1.1.0",
        "accuracy": 0.87,
        "size": 24 * 1024 * 1024,
        "agent": "AdvancedAICore",
        "framework": "JAX/Flax",
        "recommended_model": "PatchTST / TransformerBasedPolicy",
        "task": "多步时序决策 / 多模态融合推理",
        "input_dim": 256,
        "output_dim": 10,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 4. 元学习系统（MAML 思路）────────────────────────────────────────
    {
        "id": "meta_learning_v1",
        "name": "元学习快速适应模型",
        "description": "MetaLearningSystem（AdvancedAICore 子模块），MAML 风格内循环5步梯度更新，"
                       "能在少量新样本下快速适配新环境（新作物种类、新气候区）。"
                       "推荐模型：MAML + ProtoNet 结合方案（PyTorch Learn2Learn库）",
        "type": "meta_learning",
        "status": "training",
        "version": "0.8.0",
        "accuracy": 0.82,
        "size": 15 * 1024 * 1024,
        "agent": "AdvancedAICore / LearningAgent",
        "framework": "PyTorch",
        "recommended_model": "MAML (learn2learn)",
        "task": "少样本快速迁移 / 跨域环境适应",
        "inner_loop_steps": 5,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 5. 多模态好奇心驱动探索（CERMIC）────────────────────────────────
    {
        "id": "curiosity_cermic_v1",
        "name": "多模态好奇心探索模型",
        "description": "MultiModalCuriosity（CERMIC框架），PyTorch实现，融合视觉/文本/语音/传感器四路编码器。"
                       "计算内在奖励（prediction_error / information_gain），驱动 AGI 主动探索。"
                       "推荐模型：ICM（Intrinsic Curiosity Module）+ 多模态编码器（Vision:512→256, Text:512→256）",
        "type": "multimodal",
        "status": "ready",
        "version": "1.0.0",
        "accuracy": 0.84,
        "size": 56 * 1024 * 1024,
        "agent": "MultiModalCuriosity / OrganicAICore",
        "framework": "PyTorch",
        "recommended_model": "ICM (Intrinsic Curiosity Module)",
        "task": "AGI主动探索 / 新颖性评估 / 信息增益计算",
        "modality_weights": {"vision": 0.4, "text": 0.3, "speech": 0.2, "sensor": 0.1},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 6. 决策智能体风险评估（数值回归）───────────────────────────────
    {
        "id": "risk_assessment_v1",
        "name": "风险评估与有机核心决策模型",
        "description": "面向 DecisionAgent / RiskAgent 的轻量MLP风险打分网络，"
                       "输入：环境状态+历史决策序列，输出：风险评分[0,1]。"
                       "推荐模型：LightGBM（表格数据，快速推理）或 TabNet（可解释性更强）",
        "type": "risk_model",
        "status": "deployed",
        "version": "2.0.0",
        "accuracy": 0.89,
        "size": 8 * 1024 * 1024,
        "agent": "DecisionAgent / RiskAgent",
        "framework": "LightGBM",
        "recommended_model": "LightGBM / TabNet",
        "task": "环境风险评估 / 决策置信度计算 / 异常预警",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    # ── 7. 生长趋势时序预测（时间序列）──────────────────────────────────
    {
        "id": "growth_forecast_v1",
        "name": "作物生长趋势预测模型",
        "description": "基于传感器时序数据（温度/湿度/CO₂/光照强度）预测72小时内作物生长指标。"
                       "推荐模型：TimesNet 或 iTransformer（2024 SOTA时序模型，开源可本地部署，无需API）",
        "type": "time_series",
        "status": "training",
        "version": "0.9.0",
        "accuracy": 0.78,
        "size": 32 * 1024 * 1024,
        "agent": "LearningAgent / DataAgent",
        "framework": "PyTorch",
        "recommended_model": "TimesNet / iTransformer",
        "task": "作物生长预测 / 环境参数趋势分析 / 能耗优化",
        "forecast_horizon": 72,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

# 模拟训练任务
training_tasks = {}

# 模拟决策历史（15条，覆盖不同动作类型）
_decision_actions = [
    ("temperature_adjust", {"zone": "A", "target_temp": 25.5, "current_temp": 26.8}, 0.92, 0.85, True, 0.88),
    ("irrigation",         {"zone": "B", "duration": 300, "amount": 500},            0.87, 0.78, True, 0.82),
    ("light_spectrum",     {"crop": "番茄", "red": 0.6, "blue": 0.4, "intensity": 0.8}, 0.95, 0.91, True, 0.93),
    ("co2_injection",      {"greenhouse": "1", "target_level": 800, "duration": 1800}, 0.89, 0.82, True, 0.85),
    ("humidity_adjust",    {"zone": "C", "target_humidity": 65, "current_humidity": 58}, 0.84, 0.76, False, None),
    ("pest_alert",         {"zone": "A", "pest_type": "蚜虫", "severity": "low"},    0.78, 0.70, True, 0.72),
    ("fertilization",      {"zone": "B", "nutrient": "N-P-K", "amount": 200},       0.91, 0.83, True, 0.87),
    ("ventilation",        {"greenhouse": "2", "mode": "auto", "target_co2": 600},  0.86, 0.79, True, 0.81),
    ("temperature_adjust", {"zone": "B", "target_temp": 24.0, "current_temp": 22.5}, 0.90, 0.84, True, 0.86),
    ("light_spectrum",     {"crop": "生菜", "red": 0.5, "blue": 0.5, "intensity": 0.7}, 0.93, 0.88, True, 0.90),
    ("irrigation",         {"zone": "A", "duration": 240, "amount": 380},           0.82, 0.74, True, 0.77),
    ("co2_injection",      {"greenhouse": "2", "target_level": 750, "duration": 1200}, 0.88, 0.81, False, None),
    ("humidity_adjust",    {"zone": "A", "target_humidity": 70, "current_humidity": 75}, 0.85, 0.77, True, 0.80),
    ("pest_alert",         {"zone": "C", "pest_type": "白粉病", "severity": "medium"}, 0.94, 0.89, True, 0.91),
    ("fertilization",      {"zone": "C", "nutrient": "磷酸盐", "amount": 150},      0.80, 0.72, True, 0.75),
]

decision_history = []
for idx, (action, params, conf, exp_r, executed, actual_r) in enumerate(_decision_actions):
    entry = {
        "decision_id": f"dec_{idx+1:03d}",
        "timestamp": (datetime.now() - timedelta(minutes=(len(_decision_actions) - idx) * 12)).isoformat(),
        "action": action,
        "parameters": params,
        "confidence": conf,
        "expected_reward": exp_r,
        "executed": executed,
    }
    if executed and actual_r is not None:
        entry["actual_reward"] = actual_r
    else:
        entry["reason"] = "条件不满足" if not executed else "等待反馈"
    decision_history.append(entry)

# 模拟传感器数据（72小时 × 3区域，含更精细的日夜波动）
import math as _math
sensor_data_history = []
for i in range(72):  # 72小时数据
    hour_of_day = i % 24
    day_factor = _math.sin(_math.pi * hour_of_day / 12)  # 日夜变化因子
    light_on = 6 < hour_of_day < 20
    sensor_data_history.append({
        "timestamp": (datetime.now() - timedelta(hours=71-i)).isoformat(),
        "sensors": {
            "zone_a": {
                "temperature": round(24 + 2 * day_factor + (i % 3) * 0.3, 2),
                "humidity": round(62 + 8 * _math.cos(_math.pi * hour_of_day / 24), 2),
                "co2": round(420 + (i % 6) * 15 + (50 if not light_on else 0), 1),
                "light": round(600 + 300 * day_factor if light_on else 0, 1),
                "soil_moisture": round(45 + (i % 8) * 2, 1),
                "ph": round(6.5 + (i % 4) * 0.1, 2)
            },
            "zone_b": {
                "temperature": round(23 + 1.8 * day_factor + (i % 4) * 0.2, 2),
                "humidity": round(66 + 6 * _math.cos(_math.pi * hour_of_day / 24), 2),
                "co2": round(440 + (i % 5) * 12, 1),
                "light": round(550 + 280 * day_factor if light_on else 0, 1),
                "soil_moisture": round(50 + (i % 6) * 1.5, 1),
                "ph": round(6.8 + (i % 3) * 0.05, 2)
            },
            "zone_c": {
                "temperature": round(25 + 2.2 * day_factor + (i % 5) * 0.25, 2),
                "humidity": round(58 + 10 * _math.cos(_math.pi * hour_of_day / 24), 2),
                "co2": round(380 + (i % 7) * 18, 1),
                "light": round(650 + 320 * day_factor if light_on else 0, 1),
                "soil_moisture": round(42 + (i % 9) * 1.8, 1),
                "ph": round(6.3 + (i % 5) * 0.08, 2)
            }
        }
    })

# 模拟预测结果（含多作物、多维度、环境预测）
prediction_results = {
    "growth_forecast": {
        "crop_type": "番茄",
        "zone": "zone_a",
        "forecast_horizon": 72,
        "current_day": 35,
        "growth_stage": "开花期",
        "predictions": [
            {
                "hour": i+1,
                "growth_index": round(min(1.0, 0.52 + i * 0.0055), 4),
                "yield_potential": round(min(1.0, 0.75 + i * 0.003), 4),
                "confidence": round(max(0.7, 0.92 - i * 0.001), 4),
                "risk_score": round(0.15 + _math.sin(i / 12) * 0.05, 4)
            }
            for i in range(72)
        ],
        "recommendations": [
            {"priority": "high",   "time_hours": 8,  "action": "增加光照强度至800μmol/m²/s", "expected_effect": "加速开花进程约15%"},
            {"priority": "medium", "time_hours": 24, "action": "补充灌溉（约500mL/株）",       "expected_effect": "维持土壤含水量在45-55%"},
            {"priority": "medium", "time_hours": 48, "action": "追施磷钾肥",                    "expected_effect": "提升果实甜度与色泽"},
            {"priority": "low",    "time_hours": 72, "action": "检查支撑结构",                  "expected_effect": "防止茎干倒伏"}
        ]
    },
    "multi_crop_forecast": [
        {"crop": "番茄", "zone": "zone_a", "health_score": 92, "yield_forecast_kg": 4.8, "days_to_harvest": 18},
        {"crop": "生菜", "zone": "zone_b", "health_score": 88, "yield_forecast_kg": 1.2, "days_to_harvest": 7},
        {"crop": "黄瓜", "zone": "zone_c", "health_score": 85, "yield_forecast_kg": 3.5, "days_to_harvest": 22},
    ],
    "environment_forecast": {
        "next_24h": [
            {
                "hour": i+1,
                "temperature": round(24 + 2 * _math.sin(_math.pi * i / 12), 2),
                "humidity": round(63 + 7 * _math.cos(_math.pi * i / 24), 2),
                "co2_level": round(420 + (i % 6) * 10, 1)
            }
            for i in range(24)
        ],
        "summary": "未来24小时温湿度适宜，预计无极端天气风险"
    },
    "risk_assessment": {
        "overall_risk": 0.21,
        "updated_at": datetime.now().isoformat(),
        "factors": {
            "temperature_risk":  {"score": 0.12, "trend": "stable",    "description": "温度波动在正常范围内"},
            "humidity_risk":     {"score": 0.26, "trend": "rising",    "description": "Zone B湿度偏高，需关注"},
            "disease_risk":      {"score": 0.18, "trend": "stable",    "description": "无病害迹象"},
            "pest_risk":         {"score": 0.10, "trend": "declining", "description": "虫害风险持续下降"},
            "nutrient_risk":     {"score": 0.15, "trend": "stable",    "description": "养分供给正常"},
            "water_stress_risk": {"score": 0.20, "trend": "rising",    "description": "Zone A土壤含水量略低"}
        },
        "alerts": [
            {"level": "warning", "zone": "zone_b", "message": "Zone B湿度连续2小时超过75%，建议加强通风"},
            {"level": "info",    "zone": "zone_a", "message": "Zone A土壤含水量将在6小时内低于阈值"},
            {"level": "info",    "zone": "all",    "message": "当前整体环境适宜作物生长，综合评分92分"}
        ]
    }
}

# 模拟用户活动日志
activity_logs = [
    {"timestamp": (datetime.now() - timedelta(hours=3)).isoformat(), "user": "admin", "action": "登录系统", "ip": "192.168.1.100"},
    {"timestamp": (datetime.now() - timedelta(hours=2, minutes=45)).isoformat(), "user": "admin", "action": "查看模型状态", "details": "检查了organic_core_v1"},
    {"timestamp": (datetime.now() - timedelta(hours=2, minutes=30)).isoformat(), "user": "admin", "action": "执行决策", "details": "dec_001: 温度调节"},
    {"timestamp": (datetime.now() - timedelta(hours=1, minutes=15)).isoformat(), "user": "operator", "action": "查看监控", "details": "查看了摄像头画面"},
    {"timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(), "user": "admin", "action": "导出数据", "details": "导出了决策历史"},
    {"timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(), "user": "system", "action": "自动备份", "details": "配置已备份"},
]

@models_router.get("")
async def get_models():
    """获取模型列表"""
    return {
        "success": True,
        "data": models_db
    }

@models_router.get("/{model_id}")
async def get_model(model_id: str):
    """获取模型详情"""
    model = next((m for m in models_db if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {
        "success": True,
        "data": model
    }

@models_router.post("")
async def create_model(model_data: Dict[str, Any]):
    """创建模型"""
    new_model = {
        "id": f"model_{len(models_db) + 1}",
        **model_data,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    models_db.append(new_model)
    return {
        "success": True,
        "data": new_model
    }

@models_router.put("/{model_id}")
async def update_model(model_id: str, model_data: Dict[str, Any]):
    """更新模型"""
    model = next((m for m in models_db if m["id"] == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    model.update(model_data)
    model["updated_at"] = datetime.now().isoformat()
    return {
        "success": True,
        "data": model
    }

@models_router.delete("/{model_id}")
async def delete_model(model_id: str):
    """删除模型"""
    global models_db
    models_db = [m for m in models_db if m["id"] != model_id]
    return {
        "success": True,
        "data": {"message": "模型已删除"}
    }

@models_router.get("/{model_id}/versions")
async def get_model_versions(model_id: str):
    """获取模型版本列表"""
    # 每个版本都带 id 字段（与 model_id 相同，因为是同一模型的不同版本）
    versions = [
        {"id": model_id, "version": "1.0.0", "created_at": datetime.now().isoformat(), "description": "初始版本"},
        {"id": model_id, "version": "1.1.0", "created_at": datetime.now().isoformat(), "description": "性能优化"},
        {"id": model_id, "version": "2.0.0", "created_at": datetime.now().isoformat(), "description": "重大更新"}
    ]
    return {
        "success": True,
        "data": versions
    }

@models_router.post("/{model_id}/versions")
async def create_model_version(model_id: str, version_data: Dict[str, Any]):
    """创建模型版本"""
    return {
        "success": True,
        "data": {
            "id": model_id,
            "version_id": f"v_{uuid.uuid4().hex[:8]}",
            "model_id": model_id,
            **version_data,
            "created_at": datetime.now().isoformat()
        }
    }

@models_router.post("/import")
async def import_model(file: Dict[str, Any]):
    """导入模型"""
    return {
        "success": True,
        "data": {
            "model_id": f"model_{uuid.uuid4().hex[:8]}",
            "message": "模型导入成功"
        }
    }

@models_router.post("/pretrained")
async def create_pretrained_model(model_data: Dict[str, Any]):
    """创建预训练模型"""
    return {
        "success": True,
        "data": {
            "model_id": f"model_{uuid.uuid4().hex[:8]}",
            **model_data,
            "status": "ready",
            "created_at": datetime.now().isoformat()
        }
    }

@models_router.post("/{model_id}/start")
async def start_model(model_id: str):
    """启动模型"""
    return {
        "success": True,
        "data": {"message": f"模型 {model_id} 已启动"}
    }

@models_router.post("/{model_id}/pause")
async def pause_model(model_id: str):
    """暂停模型"""
    return {
        "success": True,
        "data": {"message": f"模型 {model_id} 已暂停"}
    }

@models_router.post("/{model_id}/train")
async def train_model(model_id: str, request: Dict[str, Any]):
    """训练模型"""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    training_tasks[task_id] = {
        "task_id": task_id,
        "model_id": model_id,
        "status": "running",
        "progress": 0,
        "current_step": 0,
        "total_steps": 1000,
        "stage": "数据预处理",
        "message": "训练任务已启动",
        "started_at": now,
        "completed_at": None,
        "metrics": {"loss": 0.5, "accuracy": 0.1}
    }
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "model_id": model_id,
            "status": "running",
            "progress": 0,
            "stage": "数据预处理",
            "current_step": 0,
            "total_steps": 1000,
            "started_at": now,
            "message": "训练任务已启动"
        }
    }

@models_router.get("/training/{task_id}")
async def get_training_status(task_id: str):
    """获取训练状态 - 模拟训练进度"""
    task = training_tasks.get(task_id)
    if not task:
        # 如果任务不存在，返回一个模拟的已完成任务，避免前端显示失败
        now = datetime.now().isoformat()
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "model_id": "unknown",
                "status": "completed",
                "progress": 100,
                "current_step": 1000,
                "total_steps": 1000,
                "stage": "训练完成",
                "message": "训练任务已完成",
                "started_at": now,
                "completed_at": now,
                "metrics": {"loss": 0.05, "accuracy": 0.95}
            }
        }
    
    # 模拟进度更新
    import random
    if task["status"] == "running":
        task["progress"] = min(100, task["progress"] + random.randint(5, 15))
        task["current_step"] = int(task["progress"] * 10)
        if task["progress"] < 30:
            task["stage"] = "数据预处理"
        elif task["progress"] < 60:
            task["stage"] = "模型训练"
        elif task["progress"] < 90:
            task["stage"] = "参数优化"
        else:
            task["stage"] = "模型验证"
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
        # 模拟指标变化
        task["metrics"] = {
            "loss": max(0.05, 0.5 - task["progress"] * 0.0045),
            "accuracy": min(0.95, 0.1 + task["progress"] * 0.0085)
        }
    
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "model_id": task["model_id"],
            "status": task["status"],
            "progress": task["progress"],
            "current_step": task["current_step"],
            "total_steps": task["total_steps"],
            "stage": task["stage"],
            "message": task["message"],
            "started_at": task["started_at"],
            "completed_at": task.get("completed_at"),
            "metrics": task.get("metrics")
        }
    }

# --------------------------
# AI控制API路由
# --------------------------
ai_control_router = APIRouter(prefix="/api/ai-control", tags=["ai-control"])

# 模拟设备数据
ai_devices = [
    {"id": "1", "name": "智能温控器", "type": "temperature", "status": "online", "connected": True},
    {"id": "2", "name": "湿度传感器", "type": "humidity", "status": "online", "connected": True},
    {"id": "3", "name": "光照控制器", "type": "light", "status": "offline", "connected": False},
    {"id": "4", "name": "CO2传感器", "type": "co2", "status": "online", "connected": True},
]

@ai_control_router.get("/devices")
async def get_ai_devices():
    """获取AI控制设备列表"""
    return {
        "success": True,
        "data": ai_devices
    }

@ai_control_router.get("/scan-devices")
async def scan_devices():
    """扫描设备"""
    return {
        "success": True,
        "data": ai_devices
    }

@ai_control_router.post("/device/{device_id}")
async def control_device(device_id: str, command: Dict[str, Any]):
    """控制设备"""
    return {
        "success": True,
        "data": {"message": f"设备 {device_id} 控制命令已发送", "command": command}
    }

@ai_control_router.get("/device/{device_id}/status")
async def get_device_status(device_id: str):
    """获取设备状态"""
    device = next((d for d in ai_devices if d["id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return {
        "success": True,
        "data": device
    }

@ai_control_router.post("/master-control")
async def master_control(command: Dict[str, Any]):
    """主控制命令"""
    # 兼容前端传入 activate 或 active 两种字段名
    active = command.get("active", command.get("activate", False))
    return {
        "success": True,
        "data": {"message": "主控制命令已执行", "active": active}
    }

@ai_control_router.get("/master-control/status")
async def get_master_control_status():
    """获取主控制状态"""
    return {
        "success": True,
        "data": {"master_control_active": True}
    }

@ai_control_router.post("/device/{device_id}/connection")
async def update_device_connection(device_id: str, params: Dict[str, Any]):
    """更新设备连接"""
    # 兼容前端传入 connect 或 connected 两种字段名
    connected = params.get("connected", params.get("connect", False))
    return {
        "success": True,
        "data": {"message": f"设备 {device_id} 连接已更新", "connected": connected}
    }

# --------------------------
# 决策API路由
# --------------------------
decision_router = APIRouter(prefix="/api/decision", tags=["decision"])

@decision_router.post("/agriculture")
async def agriculture_decision(request: Dict[str, Any]):
    """农业决策"""
    return {
        "success": True,
        "data": {
            "decision": "建议增加灌溉",
            "confidence": 0.85,
            "factors": ["土壤湿度低", "天气预报显示未来3天无雨"],
            "actions": ["开启灌溉系统30分钟", "监测土壤湿度变化"]
        }
    }

@decision_router.post("/risk")
async def risk_decision(request: Dict[str, Any]):
    """风险决策"""
    return {
        "success": True,
        "data": {
            "risk_level": "low",
            "risk_score": 25,
            "recommendations": ["当前风险较低，继续保持监控"]
        }
    }

@decision_router.post("/organic-core/activate-iteration")
async def activate_iteration():
    """激活迭代"""
    return {
        "success": True,
        "data": {"message": "迭代已激活", "iteration_id": str(uuid.uuid4())}
    }

@decision_router.post("/organic-core/deactivate-iteration")
async def deactivate_iteration():
    """停用迭代"""
    return {
        "success": True,
        "data": {"message": "迭代已停用"}
    }

@decision_router.get("/organic-core/status")
async def get_organic_core_status():
    """获取有机核心状态"""
    return {
        "success": True,
        "data": {
            "active": True,
            "iteration_count": 5,
            "last_update": datetime.now().isoformat()
        }
    }

@decision_router.post("/organic-core/evolve-structure")
async def evolve_structure():
    """进化结构"""
    return {
        "success": True,
        "data": {"message": "结构进化完成", "new_structure_version": "2.0"}
    }

# --------------------------
# 联邦学习API路由
# --------------------------
federated_router = APIRouter(prefix="/api/federated", tags=["federated"])

@federated_router.get("/clients")
async def get_federated_clients():
    """获取联邦学习客户端"""
    return {
        "success": True,
        "data": [
            {"id": "client_1", "name": "客户端1", "status": "online", "last_update": datetime.now().isoformat()},
            {"id": "client_2", "name": "客户端2", "status": "offline", "last_update": datetime.now().isoformat()}
        ]
    }

@federated_router.post("/clients")
async def register_client(client: Dict[str, Any]):
    """注册客户端"""
    return {
        "success": True,
        "data": {"message": "客户端已注册", "client_id": str(uuid.uuid4())}
    }

@federated_router.get("/rounds")
async def get_federated_rounds():
    """获取联邦学习轮次"""
    return {
        "success": True,
        "data": [
            {"round_id": 1, "status": "completed", "participants": 5, "accuracy": 0.92},
            {"round_id": 2, "status": "in_progress", "participants": 5, "accuracy": 0.0}
        ]
    }

@federated_router.post("/rounds")
async def start_federated_round():
    """开始联邦学习轮次"""
    return {
        "success": True,
        "data": {"message": "联邦学习轮次已开始", "round_id": 3}
    }

@federated_router.post("/rounds/{round_id}/aggregate")
async def aggregate_round(round_id: int):
    """聚合轮次结果"""
    return {
        "success": True,
        "data": {"message": f"轮次 {round_id} 聚合完成", "accuracy": 0.93}
    }

@federated_router.get("/status")
async def get_federated_status():
    """获取联邦学习状态"""
    return {
        "success": True,
        "data": {
            "status": "running",
            "current_round": 2,
            "total_clients": 5,
            "active_clients": 4
        }
    }

@federated_router.get("/privacy/status")
async def get_privacy_status():
    """获取隐私保护状态"""
    return {
        "success": True,
        "data": {
            "differential_privacy_enabled": True,
            "secure_aggregation_enabled": True,
            "epsilon": 1.0
        }
    }

@federated_router.put("/privacy/config")
async def update_privacy_config(config: Dict[str, Any]):
    """更新隐私配置"""
    return {
        "success": True,
        "data": {"message": "隐私配置已更新", "config": config}
    }

# --------------------------
# 区块链API路由
# --------------------------
blockchain_router = APIRouter(prefix="/api/blockchain", tags=["blockchain"])

@blockchain_router.get("/status")
async def get_blockchain_status():
    """获取区块链状态"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "initialized": True,
            "connected": True,
            "peers": 8,
            "latest_block": {
                "block_number": 12345,
                "transaction_count": 3891,
                "hash": "0x7f3a1b9c2e4d5f6a8b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2",
                "timestamp": datetime.now().isoformat()
            },
            "network_id": "fabric-mainnet",
            "consensus": "PBFT",
            "block_interval_ms": 2000,
            "avg_tx_latency_ms": 450,
            "timestamp": datetime.now().isoformat()
        }
    }

@blockchain_router.post("/models/{model_id}/verify")
async def verify_model(model_id: str):
    """验证模型"""
    return {
        "success": True,
        "data": {"message": f"模型 {model_id} 验证成功", "verified": True}
    }

@blockchain_router.get("/models/{model_id}/history")
async def get_model_history(model_id: str):
    """获取模型历史"""
    return {
        "success": True,
        "data": {
            "model_id": model_id,
            "history": [
                {
                    "transaction_id": f"tx_{model_id}_001",
                    "version": "1.0",
                    "action": "created",
                    "operator": "admin",
                    "timestamp": datetime.now().isoformat(),
                    "block_number": 12300
                },
                {
                    "transaction_id": f"tx_{model_id}_002",
                    "version": "1.1",
                    "action": "updated",
                    "operator": "admin",
                    "timestamp": datetime.now().isoformat(),
                    "block_number": 12345
                }
            ]
        }
    }

@blockchain_router.post("/access/grant")
async def grant_access(request: Dict[str, Any]):
    """授予访问权限"""
    return {
        "success": True,
        "data": {"message": "访问权限已授予", "grant_id": str(uuid.uuid4())}
    }

@blockchain_router.post("/access/revoke")
async def revoke_access(request: Dict[str, Any]):
    """撤销访问权限"""
    return {
        "success": True,
        "data": {"message": "访问权限已撤销"}
    }

@blockchain_router.post("/access/check")
async def check_access(request: Dict[str, Any]):
    """检查访问权限"""
    return {
        "success": True,
        "data": {"has_access": True}
    }

@blockchain_router.post("/roles/create")
async def create_role(role: Dict[str, Any]):
    """创建角色"""
    return {
        "success": True,
        "data": {"message": "角色已创建", "role_id": str(uuid.uuid4())}
    }

@blockchain_router.post("/roles/assign")
async def assign_role(request: Dict[str, Any]):
    """分配角色"""
    return {
        "success": True,
        "data": {"message": "角色已分配"}
    }

@blockchain_router.get("/contracts/status")
async def get_contracts_status():
    """获取合约状态"""
    return {
        "success": True,
        "data": {
            "total_contracts": 10,
            "active_contracts": 8,
            "pending_contracts": 2
        }
    }

# --------------------------
# JEPA-DTMPC API路由
# --------------------------
jepa_dtmpc_router = APIRouter(prefix="/api/jepa-dtmpc", tags=["jepa-dtmpc"])

@jepa_dtmpc_router.get("/status")
async def get_jepa_dtmpc_status():
    """获取JEPA-DTMPC状态"""
    return {
        "success": True,
        "data": {
            "is_active": True,
            "model_status": "running",
            "version": "1.0.0",
            "last_update": datetime.now().isoformat()
        }
    }

# 边缘计算API路由
# --------------------------
edge_router = APIRouter(prefix="/api/edge", tags=["edge"])

@edge_router.get("/devices")
async def get_edge_devices():
    """获取边缘设备"""
    return {
        "success": True,
        "data": [
            {"id": "edge_1", "name": "边缘节点1", "location": "温室A", "status": "online", "load": 45},
            {"id": "edge_2", "name": "边缘节点2", "location": "温室B", "status": "online", "load": 30}
        ]
    }

@edge_router.post("/devices/{device_id}/sync")
async def sync_edge_device(device_id: str):
    """同步边缘设备"""
    return {
        "success": True,
        "data": {"message": f"边缘设备 {device_id} 同步完成"}
    }

# --------------------------
# 推理服务API路由
# --------------------------
inference_router = APIRouter(prefix="/api/inference", tags=["inference"])

# 模拟推理历史
inference_history: List[Dict[str, Any]] = [
    {
        "id": "inf_001",
        "model_id": "model_1",
        "model_name": "作物识别模型",
        "input_summary": "图片数据 (224x224)",
        "result_summary": "番茄 (置信度: 96.2%)",
        "inference_time": 42,
        "status": "success",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "inf_002",
        "model_id": "model_2",
        "model_name": "病虫害检测模型",
        "input_summary": "图片数据 (512x512)",
        "result_summary": "检测到白粉病 (置信度: 88.5%)",
        "inference_time": 65,
        "status": "success",
        "created_at": datetime.now().isoformat()
    }
]

@inference_router.post("")
async def run_inference(request: Dict[str, Any]):
    """执行推理"""
    model_id = request.get("model_id", "model_1")
    inference_id = f"inf_{uuid.uuid4().hex[:6]}"
    result = {
        "id": inference_id,
        "model_id": model_id,
        "result": {"class": "番茄", "confidence": 0.962, "labels": ["番茄", "作物", "健康"]},
        "inference_time": 42,
        "model_version": "1.0.0",
        "status": "success",
        "created_at": datetime.now().isoformat()
    }
    inference_history.insert(0, result)
    return {"success": True, "data": result}

@inference_router.get("/history")
async def get_inference_history():
    """获取推理历史"""
    return {"success": True, "data": inference_history}


# --------------------------
# 训练任务API路由
# --------------------------
training_router = APIRouter(prefix="/api/training", tags=["training"])

# 模拟训练任务存储
training_tasks_db: Dict[str, Dict[str, Any]] = {
    "task_001": {
        "id": "task_001",
        "model_name": "作物识别模型 v2",
        "dataset": "农业图像数据集",
        "status": "completed",
        "progress": 100,
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    },
    "task_002": {
        "id": "task_002",
        "model_name": "病虫害检测模型 v3",
        "dataset": "病虫害标注数据集",
        "status": "running",
        "progress": 62,
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
}

@training_router.get("/tasks")
async def get_training_tasks():
    """获取训练任务列表"""
    return {"success": True, "data": list(training_tasks_db.values())}

@training_router.post("/tasks")
async def create_training_task(task_data: Dict[str, Any]):
    """创建训练任务"""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    new_task = {
        "id": task_id,
        "model_name": task_data.get("model_name", "未命名模型"),
        "dataset": task_data.get("dataset", "默认数据集"),
        "status": "pending",
        "progress": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        **{k: v for k, v in task_data.items() if k not in ["model_name", "dataset"]}
    }
    training_tasks_db[task_id] = new_task
    return {"success": True, "data": new_task}

@training_router.get("/tasks/{task_id}")
async def get_training_task(task_id: str):
    """获取训练任务详情"""
    task = training_tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    return {"success": True, "data": task}



# --------------------------
# 微调（Fine-Tune）API路由
# --------------------------
fine_tune_router = APIRouter(prefix="/api/v1/fine-tune", tags=["fine-tune"])


@fine_tune_router.get("/status")
async def fine_tune_status():
    """获取 OrganicAICore 状态及当前可调参数快照"""
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        status = core.get_status()
        status["tunable_params"] = {
            "exploration_rate": getattr(core, "_current_exploration_rate", 0.1),
            "exploration_min": getattr(core, "_exploration_min", 0.05),
            "exploration_decay": getattr(core, "_exploration_decay", 0.995),
            "utilization_weight": getattr(core, "_utilization_weight", 0.5),
            "iteration_interval": core.iteration_interval,
            "memory_retrieval_threshold": getattr(core, "_memory_retrieval_threshold", 0.7),
            "max_long_term_memory_size": getattr(core, "max_long_term_memory_size", 5000),
            "hardware_learning_enabled": core.hardware_learning_enabled,
            "multimodal_fusion_enabled": getattr(core, "multimodal_fusion_enabled", True),
        }
        return {"success": True, "data": status}
    except Exception as e:
        return {"success": False, "error": str(e)}


@fine_tune_router.post("/run")
async def fine_tune_run(params: Dict[str, Any]):
    """
    执行微调。传入需要调整的参数字典。
    
    示例:
    {
      "exploration_rate": 0.2,
      "iteration_interval": 30,
      "perform_evolution": true
    }
    """
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        result = await core.fine_tune(params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@fine_tune_router.post("/validate")
async def fine_tune_validate(params: Dict[str, Any]):
    """预验证参数合法性，不执行实际微调"""
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        is_valid, error_msg = core._validate_fine_tune_params(params)
        return {"is_valid": is_valid, "error_message": error_msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_FINE_TUNE_PRESETS = {
    "explore": {"exploration_rate": 0.3, "exploration_min": 0.1, "exploration_decay": 0.99},
    "exploit": {"exploration_rate": 0.05, "exploration_min": 0.02, "exploration_decay": 0.999},
    "fast":    {"iteration_interval": 15},
    "stable":  {"iteration_interval": 120},
    "evolve":  {"perform_evolution": True, "evolution_strategy": "adaptive"},
    "reset":   {
        "exploration_rate": 0.1, "exploration_min": 0.05, "exploration_decay": 0.995,
        "utilization_weight": 0.5, "iteration_interval": 60,
        "memory_retrieval_threshold": 0.7, "hardware_learning_enabled": True,
        "multimodal_fusion_enabled": True,
    },
}


@fine_tune_router.post("/quick/{preset}")
async def fine_tune_quick(preset: str):
    """
    快捷预设微调。可用预设: explore / exploit / fast / stable / evolve / reset
    """
    if preset not in _FINE_TUNE_PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"未知预设 '{preset}'，可用: {list(_FINE_TUNE_PRESETS.keys())}"
        )
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        result = await core.fine_tune(_FINE_TUNE_PRESETS[preset])
        result["preset_used"] = preset
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------
# 智能体记忆API
# --------------------------

@fine_tune_router.get("/memory")
async def get_agent_memory(limit: int = 10):
    """获取智能体学习记忆"""
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        
        # 获取记忆库
        memory_bank = core.learning_system.memory_bank
        
        # 转换为可序列化的格式
        memories = []
        for mem in memory_bank[-limit:]:  # 获取最新的记忆
            memories.append({
                "memory_id": mem.memory_id,
                "experience": mem.experience,
                "reward": mem.reward,
                "timestamp": mem.timestamp.isoformat(),
                "success": mem.success,
                "context": mem.context
            })
        
        return {
            "success": True,
            "data": {
                "total_memories": len(memory_bank),
                "returned_memories": len(memories),
                "memories": memories
            }
        }
    except Exception as e:
        # 如果出错，返回模拟数据
        return {
            "success": True,
            "data": {
                "total_memories": 0,
                "returned_memories": 0,
                "memories": [],
                "note": f"记忆系统初始化中: {str(e)}"
            }
        }


@fine_tune_router.post("/memory/simulate")
async def simulate_agent_memory(count: int = 5):
    """模拟添加学习记忆（用于测试）"""
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        from src.core.ai_organic_core import LearningMemory
        import uuid
        
        core = await get_organic_ai_core()
        
        # 模拟记忆数据
        sample_experiences = [
            {"action": "temperature_adjust", "value": 25.5, "target": "zone_A"},
            {"action": "humidity_adjust", "value": 65, "target": "zone_B"},
            {"action": "light_spectrum", "red": 0.6, "blue": 0.4, "target": "crop_1"},
            {"action": "irrigation", "duration": 300, "amount": 500, "target": "field_1"},
            {"action": "co2_injection", "level": 800, "duration": 1800, "target": "greenhouse_1"},
        ]
        
        added_memories = []
        for i in range(min(count, len(sample_experiences))):
            mem = LearningMemory(
                memory_id=f"mem_{uuid.uuid4().hex[:8]}",
                experience=sample_experiences[i],
                reward=0.5 + (i * 0.1),  # 递增的奖励
                timestamp=datetime.now(),
                success=True,
                context={"source": "simulated", "iteration": i}
            )
            core.learning_system.memory_bank.append(mem)
            added_memories.append({
                "memory_id": mem.memory_id,
                "experience": mem.experience,
                "reward": mem.reward,
                "timestamp": mem.timestamp.isoformat()
            })
        
        # 更新性能指标
        core.learning_system.update_performance_metrics(0.8, True)
        
        return {
            "success": True,
            "data": {
                "added_count": len(added_memories),
                "total_memories": len(core.learning_system.memory_bank),
                "memories": added_memories
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@fine_tune_router.delete("/memory")
async def clear_agent_memory():
    """清空智能体学习记忆"""
    try:
        from src.core.ai_organic_core import get_organic_ai_core
        core = await get_organic_ai_core()
        
        cleared_count = len(core.learning_system.memory_bank)
        core.learning_system.memory_bank.clear()
        
        return {
            "success": True,
            "data": {
                "cleared_memories": cleared_count,
                "message": "记忆已清空"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# --------------------------
# JEPA-DTMPC 扩展路由
# --------------------------



@jepa_dtmpc_router.get("/prediction")
async def get_jepa_prediction():
    """获取JEPA预测数据"""
    import math, random
    t = datetime.now().timestamp()
    return {
        "success": True,
        "data": {
            "cv_prediction": [round(0.5 + 0.3 * math.sin(t + i), 4) for i in range(5)],
            "jepa_prediction": [round(0.6 + 0.2 * math.cos(t + i), 4) for i in range(5)],
            "fused_prediction": [round(0.55 + 0.25 * math.sin(t + i + 0.5), 4) for i in range(5)],
            "energy": round(0.72 + random.uniform(-0.05, 0.05), 4),
            "weight": round(0.85 + random.uniform(-0.03, 0.03), 4),
            "embedding_dynamics": [[round(random.gauss(0, 0.1), 4) for _ in range(8)] for _ in range(3)],
            "timestamp": datetime.now().isoformat()
        }
    }

@jepa_dtmpc_router.post("/activate")
async def activate_jepa_dtmpc(params: Dict[str, Any]):
    """激活JEPA-DTMPC"""
    return {
        "success": True,
        "data": {
            "message": "JEPA-DTMPC 已激活",
            "session_id": str(uuid.uuid4()),
            "activated_at": datetime.now().isoformat()
        }
    }

@jepa_dtmpc_router.post("/train")
async def train_jepa_model():
    """启动JEPA模型训练"""
    task_id = f"jepa_task_{uuid.uuid4().hex[:8]}"
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "message": "JEPA训练任务已启动",
            "started_at": datetime.now().isoformat()
        }
    }

@jepa_dtmpc_router.get("/train/{task_id}")
async def get_jepa_training_status(task_id: str):
    """获取JEPA训练状态"""
    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "model_id": "jepa_model",
            "status": "running",
            "progress": 45,
            "stage": "特征提取",
            "current_step": 450,
            "total_steps": 1000,
            "started_at": datetime.now().isoformat(),
            "metrics": {"loss": 0.042, "accuracy": 0.918}
        }
    }


# --------------------------
# 性能监控API路由
# --------------------------
performance_router = APIRouter(prefix="/api/performance", tags=["performance"])

# 模拟告警数据
performance_alerts: List[Dict[str, Any]] = [
    {
        "id": "alert_001",
        "level": "warning",
        "component": "推理引擎",
        "message": "推理延迟超过阈值 (120ms > 100ms)",
        "acknowledged": False,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "alert_002",
        "level": "info",
        "component": "模型训练",
        "message": "训练任务已完成",
        "acknowledged": True,
        "created_at": datetime.now().isoformat()
    }
]

@performance_router.get("/summary")
async def get_performance_summary(time_range: str = "1h"):
    """获取性能摘要"""
    return {
        "success": True,
        "data": {
            "time_range": time_range,
            "avg_inference_latency_ms": 64,
            "throughput_rps": 240,
            "error_rate": 0.004,
            "model_accuracy": 0.924,
            "cpu_utilization": 0.452,
            "memory_utilization": 0.628,
            "active_nodes": 14,
            "total_nodes": 16,
            "total_requests": 12480,
            "successful_requests": 12430,
            "timestamp": datetime.now().isoformat()
        }
    }

@performance_router.get("/integration-summary")
async def get_integration_performance_summary():
    """获取集成性能摘要"""
    return {
        "success": True,
        "data": {
            "jepa_dtmpc_latency_ms": 28,
            "edge_sync_latency_ms": 15,
            "federated_round_time_s": 120,
            "blockchain_tx_time_ms": 450,
            "overall_integration_score": 0.87,
            "timestamp": datetime.now().isoformat()
        }
    }

@performance_router.get("/optimization/status")
async def get_optimization_status():
    """获取优化状态"""
    return {
        "success": True,
        "data": {
            "auto_optimization_enabled": True,
            "last_optimization_at": datetime.now().isoformat(),
            "optimizations_applied": 7,
            "performance_gain_percent": 18.5,
            "status": "active"
        }
    }

@performance_router.get("/optimization/recommendations")
async def get_optimization_recommendations():
    """获取优化建议"""
    return {
        "success": True,
        "data": [
            {
                "id": "rec_001",
                "component": "推理引擎",
                "type": "batch_size_tuning",
                "description": "增大批处理大小以提升吞吐量",
                "expected_gain_percent": 12,
                "priority": "high"
            },
            {
                "id": "rec_002",
                "component": "模型存储",
                "type": "quantization",
                "description": "对模型进行INT8量化以减少内存占用",
                "expected_gain_percent": 8,
                "priority": "medium"
            },
            {
                "id": "rec_003",
                "component": "边缘节点",
                "type": "load_balancing",
                "description": "重新分配边缘节点负载",
                "expected_gain_percent": 5,
                "priority": "low"
            }
        ]
    }

@performance_router.post("/optimization/apply")
async def apply_optimization(request: Dict[str, Any]):
    """应用优化"""
    return {
        "success": True,
        "data": {
            "message": f"优化已应用: {request.get('recommendation_type', 'unknown')}",
            "component": request.get("component", "unknown"),
            "applied_at": datetime.now().isoformat(),
            "estimated_effect": "预计在5分钟后生效"
        }
    }

@performance_router.get("/alerts")
async def get_performance_alerts():
    """获取性能告警"""
    return {"success": True, "data": performance_alerts}

@performance_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """确认告警"""
    for alert in performance_alerts:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.now().isoformat()
            return {"success": True, "data": {"message": "告警已确认", "alert_id": alert_id}}
    raise HTTPException(status_code=404, detail="告警不存在")

@performance_router.get("/benchmark/report")
async def get_benchmark_report():
    """获取基准测试报告"""
    return {
        "success": True,
        "data": {
            "report_id": f"bench_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.now().isoformat(),
            "tests": [
                {"name": "推理延迟测试", "status": "passed", "result": "64ms avg", "baseline": "100ms"},
                {"name": "吞吐量测试", "status": "passed", "result": "240 req/s", "baseline": "200 req/s"},
                {"name": "内存占用测试", "status": "passed", "result": "2.4GB", "baseline": "4GB"},
                {"name": "模型加载时间", "status": "warning", "result": "3.2s", "baseline": "2s"}
            ],
            "overall_score": 87,
            "grade": "B+"
        }
    }

@performance_router.post("/benchmark/run")
async def run_benchmark_test(request: Dict[str, Any]):
    """运行基准测试"""
    test_id = f"bench_run_{uuid.uuid4().hex[:8]}"
    return {
        "success": True,
        "data": {
            "test_id": test_id,
            "test_type": request.get("test_type", "comprehensive"),
            "status": "running",
            "message": "基准测试已启动，预计耗时2-5分钟",
            "started_at": datetime.now().isoformat()
        }
    }

@performance_router.post("/auto-optimization/enable")
async def enable_auto_optimization():
    """启用自动优化"""
    return {
        "success": True,
        "data": {"message": "自动优化已启用", "enabled_at": datetime.now().isoformat()}
    }

@performance_router.post("/auto-optimization/disable")
async def disable_auto_optimization():
    """禁用自动优化"""
    return {
        "success": True,
        "data": {"message": "自动优化已禁用", "disabled_at": datetime.now().isoformat()}
    }

@performance_router.post("/optimization/auto/run")
async def run_auto_optimization():
    """运行自动优化"""
    return {
        "success": True,
        "data": {
            "message": "自动优化任务已启动",
            "task_id": f"auto_opt_{uuid.uuid4().hex[:8]}",
            "started_at": datetime.now().isoformat()
        }
    }

@performance_router.get("/metrics/{metric_type}")
async def get_metric_details(metric_type: str, time_range: str = "1h"):
    """获取指标详情"""
    import math, random
    now = datetime.now().timestamp()
    points = []
    for i in range(20):
        t = now - (20 - i) * 180  # 每3分钟一个点
        dt = datetime.fromtimestamp(t)
        val = round(50 + 30 * math.sin(t / 3600) + random.uniform(-5, 5), 2)
        points.append({"timestamp": dt.isoformat(), "value": val})
    return {
        "success": True,
        "data": {
            "metric_type": metric_type,
            "time_range": time_range,
            "unit": "ms" if "latency" in metric_type else "%",
            "data_points": points,
            "avg": round(sum(p["value"] for p in points) / len(points), 2),
            "max": round(max(p["value"] for p in points), 2),
            "min": round(min(p["value"] for p in points), 2)
        }
    }

@performance_router.post("/metrics")
async def record_performance_metric(metric_data: Dict[str, Any]):
    """记录性能指标"""
    return {
        "success": True,
        "data": {"message": "性能指标已记录", "recorded_at": datetime.now().isoformat()}
    }

@performance_router.post("/integration-metrics")
async def record_integration_metrics(performance_data: Dict[str, Any]):
    """记录集成性能指标"""
    return {
        "success": True,
        "data": {"message": "集成性能指标已记录", "recorded_at": datetime.now().isoformat()}
    }

@performance_router.post("/migration-learning-metrics")
async def record_migration_learning_metrics(performance_data: Dict[str, Any]):
    """记录迁移学习性能指标"""
    return {
        "success": True,
        "data": {"message": "迁移学习性能指标已记录", "recorded_at": datetime.now().isoformat()}
    }

@performance_router.post("/edge-computing-metrics")
async def record_edge_computing_metrics(performance_data: Dict[str, Any]):
    """记录边缘计算性能指标"""
    return {
        "success": True,
        "data": {"message": "边缘计算性能指标已记录", "recorded_at": datetime.now().isoformat()}
    }



# --------------------------
# 多智能体系统 API 路由
# --------------------------
agents_router = APIRouter(prefix="/api/agents", tags=["multi-agent"])

# 懒加载协调者（避免启动时卡住）
_orchestrator_instance = None
_orchestrator_error: Optional[str] = None


def _get_orchestrator_lazy():
    """懒加载协调者（首次调用时初始化）"""
    global _orchestrator_instance, _orchestrator_error
    if _orchestrator_instance is None and _orchestrator_error is None:
        try:
            import sys as _sys
            _sys.path.insert(0, os.path.dirname(__file__))
            from src.orchestrator_agent import create_orchestrator
            _orchestrator_instance = create_orchestrator(timeout_seconds=30)
        except Exception as e:
            _orchestrator_error = str(e)
    return _orchestrator_instance, _orchestrator_error


@agents_router.get("/health")
async def agents_health():
    """获取所有智能体健康状态"""
    orchestrator, err = _get_orchestrator_lazy()
    if err:
        return {
            "status": "init_failed",
            "error": err,
            "timestamp": datetime.now().isoformat()
        }
    if orchestrator is None:
        return {"status": "not_initialized", "timestamp": datetime.now().isoformat()}
    return orchestrator.get_all_agents_health()


@agents_router.get("/routing")
async def agents_routing():
    """获取智能体路由配置"""
    orchestrator, err = _get_orchestrator_lazy()
    if err or orchestrator is None:
        return {"error": err or "未初始化", "routes": {}}
    return orchestrator.get_routing_config()


@agents_router.get("/tasks")
async def agents_task_history(limit: int = 20):
    """获取最近的任务执行历史"""
    orchestrator, err = _get_orchestrator_lazy()
    if err or orchestrator is None:
        return {"error": err or "未初始化", "tasks": []}
    return {
        "success": True,
        "tasks": orchestrator.get_task_history(limit=limit),
        "timestamp": datetime.now().isoformat()
    }


class NLPParseRequest(BaseModel):
    text: str
    user_id: str = "anonymous"


class DispatchRequest(BaseModel):
    intent: str
    params: Dict[str, Any] = {}
    user_id: str = "anonymous"


class CollaborativeDecisionRequest(BaseModel):
    crop_name: str = "水稻"
    location: str = "北京"
    zone: str = "zone_a"
    growth_stage: str = "分蘖期"
    user_id: str = "anonymous"
    extra: Dict[str, Any] = {}


@agents_router.post("/nlp/parse")
async def nlp_parse(req: NLPParseRequest):
    """
    NLP自然语言解析
    - 意图识别 + 实体提取 + 情感分析 + 建议回复
    """
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(__file__))
        from skills.nlp_skill import NLPSkill
        nlp = NLPSkill()
        result = nlp.parse_command(req.text)
        return {"success": True, "user_id": req.user_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP解析失败: {e}")


@agents_router.post("/recommend")
async def get_recommendations(
    user_id: str = "anonymous",
    soil_moisture: float = 45.0,
    temperature: float = 26.0,
    humidity: float = 70.0,
    light_intensity: float = 800.0,
    ph: float = 6.5,
    days_since_fertilization: int = 10,
    growth_progress: float = 0.5,
):
    """
    获取个性化农业行动推荐
    根据当前传感器数据生成优先级排序的推荐列表
    """
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(__file__))
        from skills.recommendation_skill import RecommendationSkill
        rec = RecommendationSkill()
        context = {
            "soil_moisture": soil_moisture,
            "temperature": temperature,
            "humidity": humidity,
            "light_intensity": light_intensity,
            "ph": ph,
            "days_since_fertilization": days_since_fertilization,
            "growth_progress": growth_progress
        }
        recommendations = rec.recommend_actions(user_id, context)
        return {
            "success": True,
            "user_id": user_id,
            "context": context,
            "recommendations": recommendations,
            "count": len(recommendations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐生成失败: {e}")


@agents_router.post("/dispatch")
async def dispatch_to_agent(req: DispatchRequest):
    """
    向智能体调度命令
    根据意图路由到对应专业智能体处理
    """
    orchestrator, err = _get_orchestrator_lazy()
    if err:
        raise HTTPException(status_code=503, detail=f"多智能体系统未就绪: {err}")
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="多智能体系统未初始化")
    try:
        result = await orchestrator.dispatch(req.intent, req.params, req.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调度失败: {e}")


@agents_router.post("/collaborative-decision")
async def collaborative_decision(req: CollaborativeDecisionRequest):
    """
    多智能体协同决策
    执行完整的决策流水线：传感器采集 → AI决策 → 推荐生成 → 区块链记录
    """
    orchestrator, err = _get_orchestrator_lazy()
    if err:
        raise HTTPException(status_code=503, detail=f"多智能体系统未就绪: {err}")
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="多智能体系统未初始化")
    try:
        farm_context = {
            "crop_name": req.crop_name,
            "location": req.location,
            "zone": req.zone,
            "growth_stage": req.growth_stage,
            **req.extra
        }
        result = await orchestrator.collaborative_decision(farm_context, req.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"协同决策失败: {e}")


@agents_router.get("/skills")
async def list_skills():
    """列出所有已注册的技能模块及其状态"""
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(__file__))
        from skills import SKILL_REGISTRY
        skills_info = []
        for name, cls in SKILL_REGISTRY.items():
            skills_info.append({
                "name": name,
                "class": cls.__name__,
                "module": cls.__module__,
                "status": "active",
                "description": (cls.__doc__ or "").strip().split("\n")[0]
            })
        return {
            "success": True,
            "skills": skills_info,
            "total": len(skills_info),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"技能列表获取失败: {e}")


# --------------------------
# 数据导出 API 路由
# --------------------------
export_router = APIRouter(prefix="/api/export", tags=["export"])

def _to_csv(rows: List[Dict[str, Any]]) -> str:
    """将字典列表转换为 CSV 字符串"""
    if not rows:
        return ""
    import io, csv
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()

def _flatten(d: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """递归展平嵌套字典（用于 CSV 导出）"""
    result: Dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(_flatten(v, key))
        elif isinstance(v, list):
            result[key] = str(v)
        else:
            result[key] = v
    return result

@export_router.get("/sensor-data")
async def export_sensor_data(
    fmt: str = "json",
    hours: int = 24,
    zone: Optional[str] = None
):
    """
    导出传感器历史数据
    - fmt: json | csv
    - hours: 导出最近 N 小时（最多72）
    - zone: zone_a | zone_b | zone_c | None（全部）
    """
    from fastapi.responses import Response
    hours = min(hours, 72)
    cutoff = datetime.now() - timedelta(hours=hours)
    rows = [
        r for r in sensor_data_history
        if datetime.fromisoformat(r["timestamp"]) >= cutoff
    ]
    if fmt.lower() == "csv":
        flat_rows = []
        for r in rows:
            flat = {"timestamp": r["timestamp"]}
            sensors = r.get("sensors", {})
            if zone:
                z_data = sensors.get(zone, {})
                flat.update({f"{zone}.{k}": v for k, v in z_data.items()})
            else:
                for z, z_data in sensors.items():
                    flat.update({f"{z}.{k}": v for k, v in z_data.items()})
            flat_rows.append(flat)
        csv_str = _to_csv(flat_rows)
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="sensor_data_{hours}h.csv"'}
        )
    return {
        "success": True,
        "data": {
            "export_type": "sensor_data",
            "period_hours": hours,
            "zone_filter": zone,
            "total_records": len(rows),
            "exported_at": datetime.now().isoformat(),
            "records": rows
        }
    }

@export_router.get("/decisions")
async def export_decision_history(
    fmt: str = "json",
    executed_only: bool = False
):
    """
    导出决策历史
    - fmt: json | csv
    - executed_only: 仅导出已执行的决策
    """
    from fastapi.responses import Response
    rows = decision_history
    if executed_only:
        rows = [r for r in rows if r.get("executed", False)]
    if fmt.lower() == "csv":
        flat_rows = [_flatten(r) for r in rows]
        csv_str = _to_csv(flat_rows)
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="decision_history.csv"'}
        )
    return {
        "success": True,
        "data": {
            "export_type": "decision_history",
            "executed_only": executed_only,
            "total_records": len(rows),
            "exported_at": datetime.now().isoformat(),
            "records": rows
        }
    }

@export_router.get("/models")
async def export_models(fmt: str = "json"):
    """
    导出模型列表
    - fmt: json | csv
    """
    from fastapi.responses import Response
    rows = models_db
    if fmt.lower() == "csv":
        flat_rows = [_flatten(r) for r in rows]
        csv_str = _to_csv(flat_rows)
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="models.csv"'}
        )
    return {
        "success": True,
        "data": {
            "export_type": "models",
            "total_records": len(rows),
            "exported_at": datetime.now().isoformat(),
            "records": rows
        }
    }

@export_router.get("/inference-history")
async def export_inference_history(fmt: str = "json"):
    """
    导出推理历史
    - fmt: json | csv
    """
    from fastapi.responses import Response
    rows = inference_history
    if fmt.lower() == "csv":
        flat_rows = [_flatten(r) for r in rows]
        csv_str = _to_csv(flat_rows)
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="inference_history.csv"'}
        )
    return {
        "success": True,
        "data": {
            "export_type": "inference_history",
            "total_records": len(rows),
            "exported_at": datetime.now().isoformat(),
            "records": rows
        }
    }

@export_router.get("/activity-logs")
async def export_activity_logs(fmt: str = "json"):
    """
    导出用户活动日志
    - fmt: json | csv
    """
    from fastapi.responses import Response
    rows = activity_logs
    if fmt.lower() == "csv":
        flat_rows = [_flatten(r) for r in rows]
        csv_str = _to_csv(flat_rows)
        return Response(
            content=csv_str.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="activity_logs.csv"'}
        )
    return {
        "success": True,
        "data": {
            "export_type": "activity_logs",
            "total_records": len(rows),
            "exported_at": datetime.now().isoformat(),
            "records": rows
        }
    }

@export_router.get("/full-report")
async def export_full_report():
    """导出完整系统报告（JSON格式，包含所有数据）"""
    return {
        "success": True,
        "data": {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "generated_at": datetime.now().isoformat(),
            "system_info": {
                "version": "1.0.0",
                "mode": "simulation",
                "uptime_hours": 48
            },
            "summary": {
                "total_models": len(models_db),
                "total_decisions": len(decision_history),
                "executed_decisions": sum(1 for d in decision_history if d.get("executed")),
                "sensor_data_hours": 72,
                "inference_count": len(inference_history),
                "avg_decision_confidence": round(
                    sum(d.get("confidence", 0) for d in decision_history) / max(len(decision_history), 1), 3
                )
            },
            "models": models_db,
            "recent_decisions": decision_history[-10:],
            "latest_sensor": sensor_data_history[-1] if sensor_data_history else {},
            "risk_assessment": prediction_results.get("risk_assessment", {}),
            "activity_logs": activity_logs
        }
    }

# --------------------------
# 创建应用
# --------------------------
def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    app = FastAPI(
        title="AI项目API服务",
        description="简化版API服务，提供认证和社区功能",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应限制来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(auth_router)
    app.include_router(community_router)
    app.include_router(agriculture_router)
    app.include_router(system_router)
    app.include_router(camera_router)
    app.include_router(ai_control_router)
    app.include_router(decision_router)
    app.include_router(federated_router)
    app.include_router(blockchain_router)
    app.include_router(edge_router)
    app.include_router(models_router)
    app.include_router(jepa_dtmpc_router)
    app.include_router(inference_router)
    app.include_router(training_router)
    app.include_router(performance_router)
    app.include_router(fine_tune_router)
    app.include_router(export_router)
    app.include_router(agents_router)
    
    # 根路径
    @app.get("/")
    async def root():
        return {
            "message": "AI项目API服务",
            "version": "1.0.0",
            "docs": "/docs",
            "mode": "simplified"  # 标记为简化模式
        }
    
    # 健康检查接口
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    return app

# 创建应用实例
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
