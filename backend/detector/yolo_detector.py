from dataclasses import dataclass, field
import os
import traceback
from backend.detector import BaseDetectionResult, DetectionBox

# 在导入YOLO之前设置torch.load配置
try:
    import torch
    # 设置torch.load的weights_only参数为False，解决PyTorch 2.6兼容性问题
    _original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load
except ImportError:
    pass

# 导入YOLO
try:
    print("[YOLO] 尝试导入ultralytics YOLO模块...")
    from ultralytics import YOLO
except ImportError:
    print("[YOLO] 警告: 无法导入ultralytics，部分功能可能不可用")
    YOLO = None

class YoloDetector:
    """YOLO目标检测类，负责检测人和水杯"""
    @dataclass
    class YoloResult(BaseDetectionResult):
        person_detected: bool = False
        cup_detected: bool = False

    def __init__(self):
        """初始化YOLO检测器"""
        self.model = None
        self.result = self.YoloResult()
        if YOLO is None:
            print("[YOLO] YOLO模块不可用")
            return
        model_path = os.path.join(os.path.dirname(__file__), "models", "yolo11n.pt")
        if not os.path.exists(os.path.dirname(model_path)):
            os.makedirs(os.path.dirname(model_path))
        
        # 尝试加载模型
        try:
            self.model = YOLO("yolo11n.pt")  # 使用预训练的YOLOv11模型
            # 强制切换到CUDA设备
            if torch.cuda.is_available():
                self.model.to('cuda')
                print("[YOLO] YOLO模型已切换到 CUDA 设备:", next(self.model.model.parameters()).device)
            else:
                print("[YOLO] 警告：未检测到可用的CUDA设备，YOLO将使用CPU运行。")
            print("[YOLO] YOLO模型加载成功")
        except Exception as e:
            print(f"[YOLO] 加载YOLO模型出错: {e}")

    def detect(self, frame):
        """
        检测图像中的人和水杯
        参数:
            frame: 要分析的图像帧
        返回:
            dict: 包含检测结果的字典，格式为：
                {
                    'person_detected': bool,
                    'cup_detected': bool,
                    'boxes': [],
                }
        """
        
        if self.model is None:
            return self.result
        
        try:
            yolo_result = self.model(frame, verbose=False)[0]  # 一张图片只有一个结果
            result = self.YoloResult()  # 重置结果

            for box in yolo_result.boxes:
                if box.conf[0] < 0.5:
                    continue  # 跳过置信度低的
                cls = int(box.cls[0])
                if cls == 0:  # person
                    result.person_detected = True
                elif cls == 39:  # bottle
                    result.cup_detected = True
                elif cls == 41:  # cup
                    result.cup_detected = True
                result.boxes.append(DetectionBox.from_yolo_box(box, self.model.names))
            
        except Exception as e:
            print(f"YOLO检测出错: {e}")
            traceback.print_exc()
            
        self.result = result
        return self.result
