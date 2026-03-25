"""
YOLO目标检测服务
基于 YOLOv8/YOLO11 实现农业场景的实时目标检测

核心能力：
  - 通用目标检测（YOLOv8n/s/m）
  - 农业专用场景：病害区域定位、害虫检测、作物识别
  - 实时帧检测（支持 cv2 frame 和 base64 图像）
  - 检测结果叠加绘图，返回标注图像

农业适配场景：
  - pest_detection:   害虫目标框定位（蚜虫/白粉虱/红蜘蛛等）
  - crop_disease:     病害区域检测（标注异常叶片/斑块范围）
  - growth_monitor:   植株计数与生长监控
  - general:          通用物体检测
"""

import base64
import io
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ── 配置 ─────────────────────────────────────────────────────────────────────

# 默认模型：yolov8n（速度最快）/yolov8s（均衡）/yolov8m（精度高）
YOLO_DEFAULT_MODEL   = os.getenv("YOLO_MODEL",       "yolov8n.pt")
YOLO_CONF_THRESHOLD  = float(os.getenv("YOLO_CONF",  "0.25"))   # 置信度阈值
YOLO_IOU_THRESHOLD   = float(os.getenv("YOLO_IOU",   "0.45"))   # NMS IoU阈值
YOLO_MAX_DETECTIONS  = int(os.getenv("YOLO_MAX_DET", "100"))     # 最大检测数
YOLO_IMG_SIZE        = int(os.getenv("YOLO_IMGSZ",   "640"))     # 推理图像尺寸
YOLO_DEVICE          = os.getenv("YOLO_DEVICE",       "auto")    # auto/cpu/0/cuda:0

# 农业场景自定义标签映射（COCO类别 → 中文）
_COCO_AGRI_LABELS: Dict[int, str] = {
    # 可能在农业环境中出现的COCO类别
    0:  "人员",
    15: "鸟类",
    16: "猫",
    17: "狗",
    73: "手机",
    # 其余保持英文
}


@dataclass
class Detection:
    """单个目标检测结果"""
    class_id:    int
    class_name:  str
    confidence:  float
    bbox:        Tuple[int, int, int, int]   # (x1, y1, x2, y2) 像素坐标
    bbox_norm:   Tuple[float, float, float, float]  # 归一化坐标 [0,1]
    area_ratio:  float = 0.0      # 占图像面积比例

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id":   self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox":       list(self.bbox),
            "bbox_norm":  [round(v, 4) for v in self.bbox_norm],
            "area_ratio": round(self.area_ratio, 4),
        }


@dataclass
class DetectionResult:
    """完整检测结果"""
    success:            bool
    scene:              str
    model_used:         str
    inference_time_ms:  float
    image_width:        int
    image_height:       int
    detections:         List[Detection] = field(default_factory=list)
    summary:            str = ""
    annotated_image_b64: Optional[str] = None   # 叠加标注框的图像 base64
    error:              Optional[str] = None

    @property
    def detection_count(self) -> int:
        return len(self.detections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success":            self.success,
            "scene":              self.scene,
            "model_used":         self.model_used,
            "inference_time_ms":  round(self.inference_time_ms, 2),
            "image_width":        self.image_width,
            "image_height":       self.image_height,
            "detection_count":    self.detection_count,
            "detections":         [d.to_dict() for d in self.detections],
            "summary":            self.summary,
            "annotated_image_b64": self.annotated_image_b64,
            "error":              self.error,
        }


# ── 主服务类 ──────────────────────────────────────────────────────────────────

class YOLODetectionService:
    """
    YOLOv8 目标检测服务（单例）

    使用方法：
        svc = YOLODetectionService()
        result = svc.detect_from_base64(image_b64, scene="pest_detection")
        result = svc.detect_from_frame(cv2_frame, scene="crop_disease")
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf:       float = YOLO_CONF_THRESHOLD,
        iou:        float = YOLO_IOU_THRESHOLD,
        max_det:    int   = YOLO_MAX_DETECTIONS,
        imgsz:      int   = YOLO_IMG_SIZE,
        device:     str   = YOLO_DEVICE,
    ):
        self._model_path = model_path or YOLO_DEFAULT_MODEL
        self._conf    = conf
        self._iou     = iou
        self._max_det = max_det
        self._imgsz   = imgsz
        self._device  = device
        self._model   = None          # 延迟加载
        self._model_name = Path(self._model_path).stem
        logger.info(
            f"YOLODetectionService 初始化 | 模型: {self._model_path} "
            f"| conf={conf} iou={iou} device={device}"
        )

    # ── 模型懒加载 ───────────────────────────────────────────────────────────

    def _ensure_model(self) -> Any:
        """
        首次调用时加载模型，之后复用。

        注意：项目里的 flax_patch.py monkey-patch 了 dataclasses._process_class，
        该补丁对 Flax 有效但会破坏 PyTorch 内部的 dataclass（non-default after default 错误）。
        解决方案：加载 ultralytics 前临时恢复原始函数，加载完恢复补丁。
        """
        if self._model is not None:
            return self._model

        import dataclasses as _dc
        import sys

        # 保存当前（可能是补丁后的）_process_class
        patched_fn  = _dc.__dict__.get("_process_class")
        original_fn = None

        # 尝试获取原始函数（补丁前的版本）
        try:
            import importlib
            _orig_module = importlib.import_module("dataclasses")
            # 如果模块被补丁过，源代码里的原始函数保存在 flax_patch 的 closure 里
            # 通过 closure 变量取回
            if patched_fn is not None and hasattr(patched_fn, "__code__"):
                closure_cells = getattr(patched_fn, "__closure__", None) or []
                for cell in closure_cells:
                    try:
                        v = cell.cell_contents
                        if callable(v) and getattr(v, "__name__", "") == "_process_class":
                            original_fn = v
                            break
                    except ValueError:
                        pass
        except Exception:
            pass

        # 如果找到了原始函数，临时替换
        if original_fn is not None:
            _dc._process_class = original_fn
            logger.debug("临时恢复原始 dataclasses._process_class 以兼容 PyTorch")

        try:
            from ultralytics import YOLO
            logger.info(f"正在加载 YOLO 模型: {self._model_path}")
            t0 = time.time()
            self._model = YOLO(self._model_path)
            elapsed = (time.time() - t0) * 1000
            logger.info(f"YOLO 模型加载完成，耗时 {elapsed:.0f}ms")
            return self._model

        except Exception as e:
            logger.error(f"YOLO 模型加载失败: {e}")
            raise RuntimeError(f"无法加载 YOLO 模型 [{self._model_path}]: {e}")

        finally:
            # 无论成功失败，都把补丁恢复回去
            if original_fn is not None and patched_fn is not None:
                _dc._process_class = patched_fn
                logger.debug("已恢复 flax_patch 的 dataclasses._process_class")

    # ── 公共接口 ─────────────────────────────────────────────────────────────

    def detect_from_frame(
        self,
        frame:           np.ndarray,
        scene:           str  = "general",
        return_annotated: bool = True,
    ) -> DetectionResult:
        """
        对 OpenCV BGR 帧做目标检测

        参数：
          frame           : cv2 读取的 BGR numpy 数组
          scene           : 检测场景（pest_detection/crop_disease/growth_monitor/general）
          return_annotated: 是否返回带标注框的 base64 图像
        """
        h, w = frame.shape[:2]
        model = self._ensure_model()

        t0 = time.perf_counter()
        try:
            results = model.predict(
                source    = frame,
                conf      = self._conf,
                iou       = self._iou,
                max_det   = self._max_det,
                imgsz     = self._imgsz,
                device    = None if self._device == "auto" else self._device,
                verbose   = False,
            )
        except Exception as e:
            logger.error(f"YOLO 推理失败: {e}")
            return DetectionResult(
                success=False, scene=scene, model_used=self._model_name,
                inference_time_ms=0, image_width=w, image_height=h,
                error=str(e)
            )

        inference_ms = (time.perf_counter() - t0) * 1000
        detections   = self._parse_results(results[0], w, h)
        summary      = self._build_summary(detections, scene)

        # 叠加标注框
        annotated_b64: Optional[str] = None
        if return_annotated:
            annotated_b64 = self._annotate_and_encode(results[0], frame)

        logger.info(
            f"[YOLO] 场景={scene} | 检测到 {len(detections)} 个目标 "
            f"| 耗时 {inference_ms:.1f}ms"
        )

        return DetectionResult(
            success=True,
            scene=scene,
            model_used=self._model_name,
            inference_time_ms=inference_ms,
            image_width=w,
            image_height=h,
            detections=detections,
            summary=summary,
            annotated_image_b64=annotated_b64,
        )

    def detect_from_base64(
        self,
        image_base64:    str,
        scene:           str  = "general",
        return_annotated: bool = True,
    ) -> DetectionResult:
        """
        对 base64 编码图像做目标检测

        参数：
          image_base64    : JPEG/PNG 的 base64 字符串
          scene           : 检测场景
          return_annotated: 是否返回带标注框的 base64 图像
        """
        try:
            img_bytes = base64.b64decode(image_base64)
            nparr     = np.frombuffer(img_bytes, np.uint8)
            frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("无法解码 base64 图像，请检查格式（JPEG/PNG）")
        except Exception as e:
            return DetectionResult(
                success=False, scene=scene, model_used=self._model_name,
                inference_time_ms=0, image_width=0, image_height=0,
                error=f"图像解码失败: {e}"
            )
        return self.detect_from_frame(frame, scene=scene, return_annotated=return_annotated)

    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息"""
        try:
            model = self._ensure_model()
            return {
                "model_path":  self._model_path,
                "model_name":  self._model_name,
                "conf":        self._conf,
                "iou":         self._iou,
                "imgsz":       self._imgsz,
                "device":      self._device,
                "num_classes": len(model.names) if hasattr(model, "names") else "unknown",
                "class_names": model.names if hasattr(model, "names") else {},
                "loaded":      self._model is not None,
            }
        except Exception as e:
            return {"error": str(e), "loaded": False}

    def update_thresholds(self, conf: Optional[float] = None, iou: Optional[float] = None):
        """动态调整置信度/IoU阈值"""
        if conf is not None:
            self._conf = max(0.01, min(0.99, conf))
        if iou is not None:
            self._iou = max(0.01, min(0.99, iou))
        logger.info(f"[YOLO] 阈值更新 conf={self._conf} iou={self._iou}")

    # ── 内部工具 ─────────────────────────────────────────────────────────────

    def _parse_results(
        self,
        result: Any,
        img_w:  int,
        img_h:  int,
    ) -> List[Detection]:
        """解析 ultralytics 推理结果为结构化 Detection 列表"""
        detections: List[Detection] = []
        if result.boxes is None:
            return detections

        boxes = result.boxes
        class_names: Dict[int, str] = result.names or {}

        for i in range(len(boxes)):
            cls_id   = int(boxes.cls[i].item())
            conf     = float(boxes.conf[i].item())
            xyxy     = boxes.xyxy[i].cpu().numpy().astype(int)
            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])

            # 农业中文标签覆盖
            cls_name = _COCO_AGRI_LABELS.get(cls_id) or class_names.get(cls_id, f"class_{cls_id}")

            # 归一化坐标
            bbox_norm = (
                round(x1 / img_w, 4),
                round(y1 / img_h, 4),
                round(x2 / img_w, 4),
                round(y2 / img_h, 4),
            )

            # 面积占比
            area_ratio = ((x2 - x1) * (y2 - y1)) / (img_w * img_h + 1e-6)

            detections.append(Detection(
                class_id   = cls_id,
                class_name = cls_name,
                confidence = conf,
                bbox       = (x1, y1, x2, y2),
                bbox_norm  = bbox_norm,
                area_ratio = area_ratio,
            ))

        return detections

    @staticmethod
    def _build_summary(detections: List[Detection], scene: str) -> str:
        """生成人类可读的检测摘要"""
        if not detections:
            return f"[{scene}] 未检测到目标"

        # 统计各类别数量
        class_counts: Dict[str, int] = {}
        for d in detections:
            class_counts[d.class_name] = class_counts.get(d.class_name, 0) + 1

        parts = [f"[{scene}] 共检测到 {len(detections)} 个目标："]
        for name, cnt in sorted(class_counts.items(), key=lambda x: -x[1]):
            # 最高置信度
            max_conf = max(d.confidence for d in detections if d.class_name == name)
            parts.append(f"  · {name} × {cnt}（最高置信度 {max_conf:.1%}）")

        return "\n".join(parts)

    @staticmethod
    def _annotate_and_encode(result: Any, original_frame: np.ndarray) -> Optional[str]:
        """
        将检测结果叠加到原图，返回 JPEG base64
        使用 ultralytics 内置的 plot() 方法绘制标注框
        """
        try:
            annotated = result.plot(
                conf=True,      # 显示置信度
                labels=True,    # 显示标签
                boxes=True,     # 显示边框
                line_width=2,
            )
            # plot() 返回 RGB，转回 BGR 以便 imencode
            annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode(".jpg", annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return base64.b64encode(buffer).decode("utf-8")
        except Exception as e:
            logger.warning(f"图像标注失败（不影响检测结果）: {e}")
            return None


# ── 全局单例 ──────────────────────────────────────────────────────────────────
_yolo_service: Optional[YOLODetectionService] = None


def get_yolo_service() -> YOLODetectionService:
    """FastAPI 依赖注入 / 全局获取"""
    global _yolo_service
    if _yolo_service is None:
        _yolo_service = YOLODetectionService()
    return _yolo_service


def reset_yolo_service(model_path: Optional[str] = None, **kwargs) -> YOLODetectionService:
    """重置/更换模型（支持在运行时切换模型权重）"""
    global _yolo_service
    _yolo_service = YOLODetectionService(model_path=model_path, **kwargs)
    return _yolo_service
