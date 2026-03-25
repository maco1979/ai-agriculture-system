"""
摄像头控制API路由
提供摄像头的操作接口
"""

from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import cv2
from cv2 import cvtColor, COLOR_BGR2RGB, imencode
import base64
import asyncio
import logging

from src.core.services.camera_controller import CameraController
from src.core.services.ptz_camera_controller import (
    PTZCameraController, PTZProtocol, PTZAction, get_ptz_controller
)
from src.core.services.vision_reasoning_pipeline import (
    VisionReasoningPipeline, VisionScene, get_vision_pipeline
)
from src.core.services.yolo_detection_service import (
    YOLODetectionService, get_yolo_service, reset_yolo_service
)

router = APIRouter(prefix="/camera", tags=["camera"])

# 配置日志
logger = logging.getLogger(__name__)

# 创建摄像头控制器实例
camera_controller = CameraController()

# PTZ云台控制器（延迟初始化）
ptz_controller: Optional[PTZCameraController] = None


class CameraOpenRequest(BaseModel):
    """打开摄像头请求"""
    camera_index: int = 0


class ResolutionRequest(BaseModel):
    """分辨率设置请求"""
    width: int
    height: int


class TrackingStartRequest(BaseModel):
    """启动视觉跟踪请求"""
    tracker_type: str = 'CSRT'
    initial_bbox: Optional[Tuple[int, int, int, int]] = None


class TrackingUpdateRequest(BaseModel):
    """更新跟踪对象请求"""
    new_bbox: Tuple[int, int, int, int]


class RecognitionStartRequest(BaseModel):
    """启动视觉识别请求"""
    model_type: str = 'haar'
    model_path: Optional[str] = None


class CameraResponse(BaseModel):
    """摄像头操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class FrameResponse(BaseModel):
    """帧数据响应"""
    success: bool
    message: str
    frame_base64: Optional[str] = None


@router.post("/open", response_model=CameraResponse)
async def open_camera(request: CameraOpenRequest):
    """
    打开摄像头
    
    Args:
        request: 包含摄像头索引的请求
        
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.open_camera(request.camera_index)
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={k: v for k, v in result.items() if k not in ["success", "message"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"打开摄像头失败: {str(e)}"
        )


@router.post("/close", response_model=CameraResponse)
async def close_camera():
    """
    关闭摄像头
    
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.close_camera()
        return CameraResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"关闭摄像头失败: {str(e)}"
        )


@router.get("/status", response_model=CameraResponse)
async def get_camera_status():
    """
    获取摄像头状态
    
    Returns:
        CameraResponse: 包含摄像头状态的响应
    """
    try:
        is_open = camera_controller.is_camera_open()
        return CameraResponse(
            success=True,
            message="摄像头状态查询成功",
            data={
                "is_open": is_open,
                "camera_index": camera_controller.camera_index
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询摄像头状态失败: {str(e)}"
        )


@router.get("/list", response_model=CameraResponse)
async def list_cameras():
    """
    列出可用的摄像头
    
    Returns:
        CameraResponse: 包含可用摄像头列表的响应
    """
    try:
        result = camera_controller.list_cameras()
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={"cameras": result["cameras"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出摄像头失败: {str(e)}"
        )


@router.post("/resolution", response_model=CameraResponse)
async def set_camera_resolution(request: ResolutionRequest):
    """
    设置摄像头分辨率
    
    Args:
        request: 包含目标分辨率的请求
        
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.set_resolution(request.width, request.height)
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={"resolution": result.get("resolution")}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置分辨率失败: {str(e)}"
        )


@router.get("/photo", response_model=FrameResponse)
async def take_photo():
    """
    拍摄照片
    
    Returns:
        FrameResponse: 包含拍摄照片的响应
    """
    try:
        frame = camera_controller.take_photo()
        
        if frame is None:
            return FrameResponse(
                success=False,
                message="拍摄失败，请检查摄像头是否已打开"
            )
        
        # 将BGR格式转换为RGB格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 将图像编码为JPEG格式
        _, buffer = cv2.imencode('.jpg', rgb_frame)
        
        # 转换为base64字符串
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return FrameResponse(
            success=True,
            message="拍摄成功",
            frame_base64=frame_base64
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拍摄失败: {str(e)}"
        )


@router.get("/frame", response_model=CameraResponse)
async def get_current_frame():
    """
    获取当前帧
    
    Returns:
        CameraResponse: 包含当前帧的响应
    """
    try:
        frame = camera_controller.get_current_frame()
        
        if frame is None:
            return CameraResponse(
                success=False,
                message="获取帧失败，请检查摄像头是否已打开"
            )
        
        # 将BGR格式转换为RGB格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # 将图像编码为JPEG格式，设置压缩质量为70以减少数据量
        success, buffer = cv2.imencode('.jpg', rgb_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        
        # 转换为base64字符串
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return CameraResponse(
            success=True,
            message="获取帧成功",
            data={"frame_base64": frame_base64}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取帧失败: {str(e)}"
        )


@router.post("/tracking/start", response_model=CameraResponse)
async def start_tracking(request: TrackingStartRequest):
    """
    启动视觉跟踪
    
    Args:
        request: 包含跟踪参数的请求
        
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.start_visual_tracking(
            tracker_type=request.tracker_type,
            initial_bbox=request.initial_bbox
        )
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={k: v for k, v in result.items() if k not in ["success", "message"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动视觉跟踪失败: {str(e)}"
        )


@router.post("/tracking/stop", response_model=CameraResponse)
async def stop_tracking():
    """
    停止视觉跟踪
    
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.stop_visual_tracking()
        return CameraResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止视觉跟踪失败: {str(e)}"
        )


@router.post("/tracking/update", response_model=CameraResponse)
async def update_tracking(request: TrackingUpdateRequest):
    """
    更新跟踪对象
    
    Args:
        request: 包含新边界框的请求
        
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.update_tracked_object(request.new_bbox)
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={k: v for k, v in result.items() if k not in ["success", "message"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新跟踪对象失败: {str(e)}"
        )


@router.get("/tracking/status", response_model=CameraResponse)
async def get_tracking_status():
    """
    获取视觉跟踪状态
    
    Returns:
        CameraResponse: 包含跟踪状态的响应
    """
    try:
        tracking_status = camera_controller.get_tracking_status()
        return CameraResponse(
            success=True,
            message="获取跟踪状态成功",
            data=tracking_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取跟踪状态失败: {str(e)}"
        )


@router.post("/recognition/start", response_model=CameraResponse)
async def start_recognition(request: RecognitionStartRequest):
    """
    启动视觉识别
    
    Args:
        request: 包含识别参数的请求
        
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.start_visual_recognition(
            model_type=request.model_type,
            model_path=request.model_path
        )
        return CameraResponse(
            success=result["success"],
            message=result["message"],
            data={k: v for k, v in result.items() if k not in ["success", "message"]}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动视觉识别失败: {str(e)}"
        )


@router.post("/recognition/stop", response_model=CameraResponse)
async def stop_recognition():
    """
    停止视觉识别
    
    Returns:
        CameraResponse: 操作结果
    """
    try:
        result = camera_controller.stop_visual_recognition()
        return CameraResponse(
            success=result["success"],
            message=result["message"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止视觉识别失败: {str(e)}"
        )


@router.get("/recognition/status", response_model=CameraResponse)
async def get_recognition_status():
    """
    获取视觉识别状态
    
    Returns:
        CameraResponse: 包含识别状态的响应
    """
    try:
        recognition_status = camera_controller.get_recognition_status()
        return CameraResponse(
            success=True,
            message="获取识别状态成功",
            data=recognition_status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取识别状态失败: {str(e)}"
        )


# ===== WebSocket 摄像头帧流接口（解决429限流问题）=====
@router.websocket("/ws/frame")
async def websocket_camera_frame(websocket: WebSocket):
    """
    WebSocket 摄像头帧流接口
    后端主动推送帧数据，避免前端高频轮询
    
    使用方法：
    const ws = new WebSocket("ws://127.0.0.1:8005/api/camera/ws/frame");
    ws.onmessage = (event) => {
        const frameData = JSON.parse(event.data);
        if (frameData.success) {
            // 使用 frameData.frame_base64
        }
    };
    """
    await websocket.accept()
    logger.info(f"WebSocket 客户端连接: {websocket.client}")
    
    try:
        # 设置帧率（30FPS = 33.3ms/帧）
        frame_interval = 1.0 / 30  # 30 FPS
        
        while True:
            try:
                # 获取当前帧
                frame = camera_controller.get_current_frame()
                
                if frame is not None:
                    # 转换为RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # 压缩编码（质量70，减少带宽）
                    success, buffer = cv2.imencode('.jpg', rgb_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    
                    if success:
                        # base64编码
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # 发送JSON格式数据
                        await websocket.send_json({
                            "success": True,
                            "frame_base64": frame_base64,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                else:
                    # 摄像头未开启或读取失败
                    await websocket.send_json({
                        "success": False,
                        "message": "摄像头未开启或读取失败"
                    })
                
                # 控制帧率
                await asyncio.sleep(frame_interval)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket 客户端断开: {websocket.client}")
                break
            except Exception as e:
                logger.error(f"WebSocket 帧处理错误: {e}")
                await websocket.send_json({
                    "success": False,
                    "message": f"帧处理错误: {str(e)}"
                })
                await asyncio.sleep(frame_interval)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接关闭: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket 连接错误: {e}")


# ==================== PTZ云台摄像头控制API ====================

class PTZConnectRequest(BaseModel):
    """PTZ连接请求"""
    protocol: str = "pelco_d"  # pelco_d, pelco_p, visca, onvif, http
    connection_type: str = "serial"  # serial, network, http
    
    # 串口参数
    port: Optional[str] = None
    baudrate: Optional[int] = 9600
    address: Optional[int] = 1
    
    # 网络参数
    host: Optional[str] = None
    network_port: Optional[int] = None
    
    # HTTP参数
    base_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class PTZActionRequest(BaseModel):
    """PTZ动作请求"""
    action: str  # pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, stop, etc.
    speed: int = 50  # 0-100
    preset_id: Optional[int] = None  # 预置位编号


class PTZPositionRequest(BaseModel):
    """PTZ位置请求"""
    pan: float  # 水平角度 (-180 to 180)
    tilt: float  # 垂直角度 (-90 to 90)
    zoom: Optional[float] = None  # 变焦倍数
    speed: int = 50


class PTZPresetRequest(BaseModel):
    """PTZ预置位请求"""
    preset_id: int
    name: Optional[str] = None


class PTZPatrolRequest(BaseModel):
    """PTZ巡航请求"""
    presets: list  # [1, 2, 3, ...]
    dwell_time: int = 5  # 每个位置停留时间（秒）


@router.post("/ptz/connect", response_model=CameraResponse)
async def ptz_connect(request: PTZConnectRequest):
    """
    连接PTZ云台摄像头
    
    支持的协议：
    - pelco_d: Pelco-D协议（最常用）
    - pelco_p: Pelco-P协议
    - visca: VISCA协议（Sony等）
    - onvif: ONVIF标准协议
    - http: HTTP API接口
    
    支持的连接类型：
    - serial: 串口连接（RS-485/RS-232）
    - network: 网络连接（TCP/IP）
    - http: HTTP接口
    """
    global ptz_controller
    
    try:
        # 参数校验层：验证必需参数
        if not request.protocol:
            return CameraResponse(
                success=False,
                message="协议类型不能为空。支持的协议: pelco_d, pelco_p, visca, onvif, http",
                data={}
            )
        if not request.connection_type:
            return CameraResponse(
                success=False,
                message="连接类型不能为空。支持的类型: serial, network, http",
                data={}
            )
        
        # 解析协议
        protocol_map = {
            "pelco_d": PTZProtocol.PELCO_D,
            "pelco_p": PTZProtocol.PELCO_P,
            "visca": PTZProtocol.VISCA,
            "onvif": PTZProtocol.ONVIF,
            "http": PTZProtocol.HTTP_API
        }
        
        protocol = protocol_map.get(request.protocol.lower())
        if not protocol:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的协议: {request.protocol}。支持的协议: pelco_d, pelco_p, visca, onvif, http"
            )
        
        # 准备连接参数
        connection_params = {}
        
        if request.connection_type == "serial":
            if not request.port:
                raise HTTPException(status_code=400, detail="串口连接需要提供port参数（如COM3）")
            connection_params = {
                "port": request.port,
                "baudrate": request.baudrate or 9600,
                "address": request.address or 1
            }
            logger.info(f"准备串口连接 - 端口:{request.port}, 波特率:{connection_params['baudrate']}")
            
        elif request.connection_type == "network":
            if not request.host or not request.network_port:
                raise HTTPException(status_code=400, detail="网络连接需要提供host和network_port参数")
            connection_params = {
                "host": request.host,
                "port": request.network_port,
                "address": request.address or 1
            }
            logger.info(f"准备网络连接 - 主机:{request.host}:{request.network_port}")
            
        elif request.connection_type == "http":
            if not request.base_url:
                raise HTTPException(status_code=400, detail="HTTP连接需要提供base_url参数")
            if not request.username or not request.password:
                raise HTTPException(status_code=400, detail="HTTP连接需要提供用户名和密码")
            connection_params = {
                "base_url": request.base_url,
                "username": request.username,
                "password": request.password
            }
            logger.info(f"准备HTTP连接 - URL:{request.base_url}")
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的连接类型: {request.connection_type}。支持的类型: serial, network, http"
            )
        
        # 对象判空层：创建PTZ控制器
        try:
            ptz_controller = PTZCameraController(
                protocol=protocol,
                connection_type=request.connection_type,
                **connection_params
            )
        except Exception as e:
            logger.error(f"PTZ控制器初始化失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"PTZ控制器初始化失败: {str(e)}"
            )
        
        # 判空检查
        if not ptz_controller:
            raise HTTPException(
                status_code=500,
                detail="PTZ控制器创建失败，对象为空"
            )
        
        # 全局异常层：执行连接
        try:
            result = await ptz_controller.connect()
        except Exception as e:
            logger.error(f"PTZ设备连接执行异常: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"PTZ设备连接失败: {str(e)}。请检查设备是否开启、线缆是否连接、端口/IP是否正确"
            )
        
        # 检查连接结果
        if result and result.get("success"):
            logger.info(f"PTZ云台连接成功: {request.protocol}@{request.connection_type}")
            return CameraResponse(
                success=True,
                message="PTZ云台连接成功",
                data=result.get("connection_info", {})
            )
        else:
            error_msg = result.get("message", "未知错误") if result else "连接返回结果为空"
            logger.error(f"PTZ连接失败: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"PTZ连接失败: {error_msg}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PTZ连接未捕获异常: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PTZ连接错误: {str(e)}"
        )


@router.post("/ptz/disconnect", response_model=CameraResponse)
async def ptz_disconnect():
    """
    断开PTZ云台连接
    """
    global ptz_controller
    
    if not ptz_controller:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        result = await ptz_controller.disconnect()
        
        if result["success"]:
            ptz_controller = None
            return CameraResponse(
                success=True,
                message="PTZ云台已断开"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"断开失败: {result['message']}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PTZ断开错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PTZ断开错误: {str(e)}"
        )


@router.post("/ptz/action", response_model=CameraResponse)
async def ptz_action(request: PTZActionRequest):
    """
    执行PTZ云台动作
    
    支持的动作：
    - pan_left: 向左转
    - pan_right: 向右转
    - tilt_up: 向上转
    - tilt_down: 向下转
    - zoom_in: 拉近
    - zoom_out: 拉远
    - focus_near: 近焦
    - focus_far: 远焦
    - iris_open: 光圈开
    - iris_close: 光圈关
    - stop: 停止
    - preset_set: 设置预置位（需要preset_id）
    - preset_goto: 转到预置位（需要preset_id）
    - auto_scan: 自动扫描
    - patrol: 巡航
    """
    global ptz_controller
    
    if not ptz_controller or not ptz_controller.is_connected:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        # 解析动作
        action_map = {
            "pan_left": PTZAction.PAN_LEFT,
            "pan_right": PTZAction.PAN_RIGHT,
            "tilt_up": PTZAction.TILT_UP,
            "tilt_down": PTZAction.TILT_DOWN,
            "zoom_in": PTZAction.ZOOM_IN,
            "zoom_out": PTZAction.ZOOM_OUT,
            "focus_near": PTZAction.FOCUS_NEAR,
            "focus_far": PTZAction.FOCUS_FAR,
            "iris_open": PTZAction.IRIS_OPEN,
            "iris_close": PTZAction.IRIS_CLOSE,
            "preset_set": PTZAction.PRESET_SET,
            "preset_goto": PTZAction.PRESET_GOTO,
            "auto_scan": PTZAction.AUTO_SCAN,
            "patrol": PTZAction.PATROL,
            "stop": PTZAction.STOP
        }
        
        action = action_map.get(request.action.lower())
        if not action:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的动作: {request.action}"
            )
        
        # 执行动作
        params = {}
        if request.preset_id is not None:
            params["preset_id"] = request.preset_id
        
        result = await ptz_controller.execute_action(
            action=action,
            speed=request.speed,
            **params
        )
        
        if result["success"]:
            return CameraResponse(
                success=True,
                message=result["message"],
                data=result.get("new_state")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"动作执行失败: {result['message']}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PTZ动作执行错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PTZ动作执行错误: {str(e)}"
        )


@router.post("/ptz/move", response_model=CameraResponse)
async def ptz_move_to_position(request: PTZPositionRequest):
    """
    移动PTZ云台到指定位置（绝对位置控制）
    
    参数：
    - pan: 水平角度 (-180 to 180)
    - tilt: 垂直角度 (-90 to 90)
    - zoom: 变焦倍数（可选）
    - speed: 移动速度 (0-100)
    """
    global ptz_controller
    
    if not ptz_controller or not ptz_controller.is_connected:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        result = await ptz_controller.move_to_position(
            pan=request.pan,
            tilt=request.tilt,
            zoom=request.zoom,
            speed=request.speed
        )
        
        if result["success"]:
            return CameraResponse(
                success=True,
                message=result["message"],
                data=result.get("current_position")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"移动失败: {result['message']}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PTZ移动错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PTZ移动错误: {str(e)}"
        )


@router.post("/ptz/preset/set", response_model=CameraResponse)
async def ptz_set_preset(request: PTZPresetRequest):
    """
    设置PTZ预置位
    
    参数：
    - preset_id: 预置位编号 (1-256)
    - name: 预置位名称（可选）
    """
    global ptz_controller
    
    if not ptz_controller or not ptz_controller.is_connected:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        result = await ptz_controller.set_preset(
            preset_id=request.preset_id,
            name=request.name
        )
        
        if result["success"]:
            return CameraResponse(
                success=True,
                message=result["message"],
                data=result.get("preset")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"设置预置位失败: {result['message']}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置预置位错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"设置预置位错误: {str(e)}"
        )


@router.post("/ptz/preset/goto", response_model=CameraResponse)
async def ptz_goto_preset(request: PTZPresetRequest):
    """
    转到PTZ预置位
    
    参数：
    - preset_id: 预置位编号
    """
    global ptz_controller
    
    if not ptz_controller or not ptz_controller.is_connected:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        result = await ptz_controller.goto_preset(preset_id=request.preset_id)
        
        if result["success"]:
            return CameraResponse(
                success=True,
                message=result["message"],
                data={
                    "preset": result.get("preset"),
                    "position": result.get("current_position")
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"转到预置位失败: {result['message']}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转到预置位错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"转到预置位错误: {str(e)}"
        )


@router.post("/ptz/patrol", response_model=CameraResponse)
async def ptz_auto_patrol(request: PTZPatrolRequest):
    """
    PTZ自动巡航（依次访问多个预置位）
    
    参数：
    - presets: 预置位列表 [1, 2, 3, ...]
    - dwell_time: 每个位置停留时间（秒）
    """
    global ptz_controller
    
    if not ptz_controller or not ptz_controller.is_connected:
        raise HTTPException(status_code=400, detail="PTZ云台未连接")
    
    try:
        # 异步启动巡航任务
        asyncio.create_task(
            ptz_controller.auto_patrol(
                presets=request.presets,
                dwell_time=request.dwell_time
            )
        )
        
        return CameraResponse(
            success=True,
            message=f"巡航任务已启动，将访问{len(request.presets)}个预置位",
            data={
                "presets": request.presets,
                "dwell_time": request.dwell_time
            }
        )
    
    except Exception as e:
        logger.error(f"启动巡航错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"启动巡航错误: {str(e)}"
        )


@router.get("/ptz/status", response_model=CameraResponse)
async def ptz_get_status():
    """
    获取PTZ云台当前状态
    
    返回：
    - connected: 连接状态
    - protocol: 协议类型
    - connection_type: 连接类型
    - position: 当前位置 {pan, tilt, zoom}
    - presets: 已设置的预置位
    """
    global ptz_controller
    
    if not ptz_controller:
        return CameraResponse(
            success=True,
            message="PTZ云台未连接",
            data={"connected": False}
        )
    
    try:
        status = ptz_controller.get_status()
        
        return CameraResponse(
            success=True,
            message="获取状态成功",
            data=status
        )
    
    except Exception as e:
        logger.error(f"获取PTZ状态错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取状态错误: {str(e)}"
        )


# ════════════════════════════════════════════════════════════════════════════
# 📷  视觉推理管线接口：拍照 → 视觉模型理解 → DeepSeek-R1 深度分析
# ════════════════════════════════════════════════════════════════════════════

class AnalyzePhotoRequest(BaseModel):
    """实时拍照分析请求（使用当前摄像头拍照）"""
    scene: str = "crop_disease"          # crop_disease / growth_status / pest_detection / environment / general
    extra_context: Optional[str] = None  # 补充背景（作物种类、环境数据等）
    vision_model: Optional[str] = None   # 覆盖默认视觉模型（留空用配置默认值）
    skip_reasoning: bool = False         # True=只做视觉理解，跳过R1（调试用）


class AnalyzeImageRequest(BaseModel):
    """上传图像分析请求（传入base64图像）"""
    image_base64: str                    # base64编码的JPEG/PNG图像
    scene: str = "crop_disease"
    extra_context: Optional[str] = None
    vision_model: Optional[str] = None
    skip_reasoning: bool = False


class VisionAnalysisResponse(BaseModel):
    """视觉推理管线响应"""
    success: bool
    scene: str
    vision_model_used: str
    reasoning_model_used: str
    vision_observation: str   # Step1：视觉AI观察报告
    reasoning_process: str    # Step2：R1思维链（CoT）
    conclusion: str           # 最终分析结论
    full_report: str          # 完整报告（Markdown格式）
    usage: dict


def _parse_scene(scene_str: str) -> VisionScene:
    """解析场景字符串，无效则回退到 general"""
    try:
        return VisionScene(scene_str)
    except ValueError:
        return VisionScene.GENERAL


@router.post(
    "/analyze-photo",
    response_model=VisionAnalysisResponse,
    summary="📷 实时拍照 → 视觉理解 → R1深度分析",
    description=(
        "使用当前摄像头实时拍照，经过两阶段AI分析：\n"
        "- **Step1**: 视觉模型（MiniCPM-V/LLaVA）理解图像内容\n"
        "- **Step2**: DeepSeek-R1:70b 对视觉结果进行深度推理分析\n\n"
        "**支持场景**: crop_disease（病害）| growth_status（生长）| "
        "pest_detection（害虫）| environment（环境）| general（通用）"
    ),
)
async def analyze_live_photo(
    request: AnalyzePhotoRequest,
    pipeline: VisionReasoningPipeline = Depends(get_vision_pipeline),
):
    """
    实时拍照视觉推理管线
    
    要求摄像头已通过 /camera/open 打开。
    """
    try:
        # Step0: 拍照
        frame = camera_controller.take_photo()
        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="摄像头未打开或拍照失败，请先调用 /camera/open"
            )

        # 转换为 base64
        import cv2 as _cv2
        _, buffer = _cv2.imencode(".jpg", frame, [int(_cv2.IMWRITE_JPEG_QUALITY), 85])
        image_b64 = base64.b64encode(buffer).decode("utf-8")

        # Step1+2: 管线分析
        scene = _parse_scene(request.scene)
        result = await pipeline.analyze(
            image_base64=image_b64,
            scene=scene,
            extra_context=request.extra_context,
            vision_model=request.vision_model,
            skip_reasoning=request.skip_reasoning,
        )

        return VisionAnalysisResponse(success=True, **result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实时拍照分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"视觉分析管线错误: {str(e)}")


@router.post(
    "/analyze-image",
    response_model=VisionAnalysisResponse,
    summary="🖼️ 上传图像 → 视觉理解 → R1深度分析",
    description="传入base64图像，不需要摄像头，适合前端上传历史照片分析。",
)
async def analyze_uploaded_image(
    request: AnalyzeImageRequest,
    pipeline: VisionReasoningPipeline = Depends(get_vision_pipeline),
):
    """
    上传图像视觉推理管线
    
    适用场景：
    - 前端上传田间巡检照片
    - 分析历史存档图像
    - 离线拍照后补充分析
    """
    try:
        scene = _parse_scene(request.scene)
        result = await pipeline.analyze(
            image_base64=request.image_base64,
            scene=scene,
            extra_context=request.extra_context,
            vision_model=request.vision_model,
            skip_reasoning=request.skip_reasoning,
        )
        return VisionAnalysisResponse(success=True, **result)

    except Exception as e:
        logger.error(f"图像分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"视觉分析管线错误: {str(e)}")


# ════════════════════════════════════════════════════════════════════════════
# 🎯  YOLOv8 目标检测接口
#     - /camera/yolo/detect-photo    : 实时拍照 → YOLO检测
#     - /camera/yolo/detect-image    : 上传图像 → YOLO检测
#     - /camera/yolo/detect-frame    : 当前帧   → YOLO检测（轻量快速）
#     - /camera/yolo/model-info      : 查看模型信息
#     - /camera/yolo/set-model       : 运行时切换模型
#     - /camera/yolo/set-thresholds  : 调整检测阈值
# ════════════════════════════════════════════════════════════════════════════

from fastapi import Depends as _Depends


class YOLODetectPhotoRequest(BaseModel):
    """实时拍照 YOLO 检测请求"""
    scene: str = "general"          # general/pest_detection/crop_disease/growth_monitor
    return_annotated: bool = True   # 是否返回标注图像


class YOLODetectImageRequest(BaseModel):
    """上传图像 YOLO 检测请求"""
    image_base64: str               # base64 编码的 JPEG/PNG 图像
    scene: str = "general"
    return_annotated: bool = True


class YOLOSetModelRequest(BaseModel):
    """切换 YOLO 模型请求"""
    model_path: str                 # 如 yolov8n.pt / yolov8s.pt / yolov8m.pt / 自定义路径
    conf: Optional[float] = None
    iou: Optional[float] = None


class YOLOSetThresholdsRequest(BaseModel):
    """调整检测阈值请求"""
    conf: Optional[float] = None    # 置信度阈值 0.01~0.99
    iou: Optional[float] = None     # NMS IoU 阈值 0.01~0.99


class YOLODetectionResponse(BaseModel):
    """YOLO 检测结果响应"""
    success: bool
    scene: str
    model_used: str
    inference_time_ms: float
    image_width: int
    image_height: int
    detection_count: int
    detections: list
    summary: str
    annotated_image_b64: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/yolo/detect-photo",
    response_model=YOLODetectionResponse,
    summary="📸 实时拍照 → YOLO目标检测",
    description=(
        "使用摄像头实时拍照，通过 YOLOv8 进行目标检测。\n\n"
        "**场景（scene）**:\n"
        "- `pest_detection`: 害虫检测\n"
        "- `crop_disease`:   病害区域定位\n"
        "- `growth_monitor`: 植株计数\n"
        "- `general`:        通用检测\n\n"
        "**推理速度**: YOLOv8n 约 10-30ms（GPU）| 50-100ms（CPU）"
    ),
)
async def yolo_detect_live_photo(
    request: YOLODetectPhotoRequest,
    yolo: YOLODetectionService = _Depends(get_yolo_service),
):
    """实时拍照后用 YOLO 进行目标检测"""
    try:
        frame = camera_controller.take_photo()
        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="摄像头未打开或拍照失败，请先调用 /camera/open"
            )
        result = yolo.detect_from_frame(
            frame, scene=request.scene, return_annotated=request.return_annotated
        )
        return YOLODetectionResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YOLO 实时检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO 检测错误: {str(e)}")


@router.post(
    "/yolo/detect-image",
    response_model=YOLODetectionResponse,
    summary="🖼️ 上传图像 → YOLO目标检测",
    description="传入 base64 图像，不依赖摄像头，适合历史照片离线检测。",
)
async def yolo_detect_uploaded_image(
    request: YOLODetectImageRequest,
    yolo: YOLODetectionService = _Depends(get_yolo_service),
):
    """上传图像的 YOLO 目标检测"""
    try:
        result = yolo.detect_from_base64(
            request.image_base64,
            scene=request.scene,
            return_annotated=request.return_annotated,
        )
        return YOLODetectionResponse(**result.to_dict())
    except Exception as e:
        logger.error(f"YOLO 图像检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO 检测错误: {str(e)}")


@router.post(
    "/yolo/detect-frame",
    response_model=YOLODetectionResponse,
    summary="⚡ 当前帧 → YOLO检测（最快）",
    description=(
        "直接对摄像头当前帧做检测，无需拍照保存。\n"
        "适合持续监控场景，延迟最低。"
    ),
)
async def yolo_detect_current_frame(
    request: YOLODetectPhotoRequest,
    yolo: YOLODetectionService = _Depends(get_yolo_service),
):
    """对摄像头当前帧做 YOLO 检测"""
    try:
        frame = camera_controller.get_current_frame()
        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="摄像头未打开或无帧数据，请先调用 /camera/open"
            )
        result = yolo.detect_from_frame(
            frame, scene=request.scene, return_annotated=request.return_annotated
        )
        return YOLODetectionResponse(**result.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YOLO 帧检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO 检测错误: {str(e)}")


@router.get(
    "/yolo/model-info",
    summary="📋 查看当前 YOLO 模型信息",
)
async def yolo_get_model_info(
    yolo: YOLODetectionService = _Depends(get_yolo_service),
):
    """返回当前加载的 YOLO 模型信息"""
    return yolo.get_model_info()


@router.post(
    "/yolo/set-model",
    summary="🔄 运行时切换 YOLO 模型",
    description=(
        "在不重启服务的情况下切换 YOLO 模型权重。\n\n"
        "**常用模型**:\n"
        "- `yolov8n.pt`: 最快（~6ms GPU），适合实时监控\n"
        "- `yolov8s.pt`: 均衡速度精度\n"
        "- `yolov8m.pt`: 更高精度，适合精细检测\n"
        "- `yolov8l.pt`: 大模型高精度\n"
        "- 自定义农业模型路径：如 `models/plant_disease.pt`"
    ),
)
async def yolo_set_model(request: YOLOSetModelRequest):
    """切换 YOLO 模型"""
    try:
        kwargs = {}
        if request.conf is not None:
            kwargs["conf"] = request.conf
        if request.iou is not None:
            kwargs["iou"] = request.iou
        svc = reset_yolo_service(model_path=request.model_path, **kwargs)
        info = svc.get_model_info()
        return {"success": True, "message": f"模型已切换为 {request.model_path}", "model_info": info}
    except Exception as e:
        logger.error(f"切换 YOLO 模型失败: {e}")
        raise HTTPException(status_code=500, detail=f"模型切换失败: {str(e)}")


@router.post(
    "/yolo/set-thresholds",
    summary="⚙️ 调整 YOLO 检测阈值",
    description=(
        "动态调整置信度和 IoU 阈值。\n\n"
        "- **conf**（置信度）低 → 检测更多目标，但误报增加；高 → 检测更精准，可能漏检\n"
        "- **iou**（NMS IoU）低 → 重叠框更少；高 → 允许更多重叠框\n"
        "推荐：conf=0.25~0.5，iou=0.45"
    ),
)
async def yolo_set_thresholds(
    request: YOLOSetThresholdsRequest,
    yolo: YOLODetectionService = _Depends(get_yolo_service),
):
    """动态调整 YOLO 检测阈值"""
    yolo.update_thresholds(conf=request.conf, iou=request.iou)
    return {
        "success": True,
        "message": "阈值已更新",
        "conf": yolo._conf,
        "iou":  yolo._iou,
    }


# ════════════════════════════════════════════════════════════════════════════
# 🔗  YOLO + 视觉推理管线联合分析
#     YOLO 快速定位目标 → minicpm-v 精细理解 → R1 深度分析
# ════════════════════════════════════════════════════════════════════════════

class YOLOPipelineRequest(BaseModel):
    """YOLO + 视觉推理联合分析请求"""
    scene: str = "crop_disease"
    extra_context: Optional[str] = None
    skip_reasoning: bool = False
    yolo_conf: Optional[float] = None   # 临时覆盖置信度


class YOLOPipelineResponse(BaseModel):
    """联合分析响应"""
    success: bool
    yolo_result: dict           # YOLO 快速检测结果
    vision_result: dict         # 视觉推理管线结果（含R1分析）
    combined_summary: str       # 综合摘要


@router.post(
    "/yolo/analyze-combined",
    response_model=YOLOPipelineResponse,
    summary="🔗 YOLO + 视觉AI + R1 三级联合分析",
    description=(
        "最完整的分析管线：\n\n"
        "1. **YOLO**：毫秒级目标定位，输出检测框和目标类别\n"
        "2. **MiniCPM-V**：深度理解图像内容和病害特征\n"
        "3. **DeepSeek-R1**：基于前两步结果进行深度推理和防治建议\n\n"
        "适合需要同时知道\"在哪里\"（YOLO定位）和\"是什么/怎么处理\"（视觉+推理）的场景。"
    ),
)
async def yolo_combined_analysis(
    request: YOLOPipelineRequest,
    yolo: YOLODetectionService = _Depends(get_yolo_service),
    pipeline: VisionReasoningPipeline = _Depends(get_vision_pipeline),
):
    """YOLO 目标检测 + 视觉推理管线三级联合分析"""
    try:
        # Step0: 拍照
        frame = camera_controller.take_photo()
        if frame is None:
            raise HTTPException(
                status_code=400,
                detail="摄像头未打开或拍照失败，请先调用 /camera/open"
            )

        # 转 base64
        _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        image_b64 = base64.b64encode(buffer).decode("utf-8")

        # Step1: YOLO 快速检测
        if request.yolo_conf:
            yolo.update_thresholds(conf=request.yolo_conf)
        yolo_result = yolo.detect_from_frame(frame, scene=request.scene, return_annotated=True)

        # Step2+3: 视觉推理管线（含 minicpm-v + R1）
        # 把 YOLO 检测摘要注入 extra_context，让 minicpm-v 能结合定位信息分析
        yolo_context = yolo_result.summary
        combined_context = (
            f"[YOLO检测结果] {yolo_context}"
            + (f"\n[补充背景] {request.extra_context}" if request.extra_context else "")
        )
        from src.core.services.vision_reasoning_pipeline import VisionScene as _VS
        try:
            scene_enum = _VS(request.scene)
        except ValueError:
            scene_enum = _VS.GENERAL

        vision_r = await pipeline.analyze(
            image_base64   = image_b64,
            scene          = scene_enum,
            extra_context  = combined_context,
            skip_reasoning = request.skip_reasoning,
        )

        # 综合摘要
        det_cnt = yolo_result.detection_count
        combined_summary = (
            f"YOLO检测到 {det_cnt} 个目标。\n"
            f"{yolo_result.summary}\n\n"
            f"视觉AI分析结论：{vision_r.get('conclusion', '（已跳过R1）')[:300]}"
        )

        return YOLOPipelineResponse(
            success=True,
            yolo_result=yolo_result.to_dict(),
            vision_result=vision_r,
            combined_summary=combined_summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"联合分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"联合分析管线错误: {str(e)}")
