import os
import re
import numpy as np
from typing import Optional, TypedDict
import cv2
import time
import traceback

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
    from ultralytics import YOLO
except ImportError:
    print("警告: 无法导入ultralytics，部分功能可能不可用")
    YOLO = None

class YoloDetector:
    """YOLO目标检测类，负责检测人和水杯"""

    class DetectionResult(TypedDict):
        person_detected: bool
        cup_detected: bool
        annotated_frame: Optional[np.ndarray]
    def __init__(self):
        """初始化YOLO检测器"""
        self.model = None
        self.result: YoloDetector.DetectionResult = {
            'person_detected': False,
            'cup_detected': False,
            'annotated_frame': None
        }
        if YOLO is not None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
            if not os.path.exists(os.path.dirname(model_path)):
                os.makedirs(os.path.dirname(model_path))
            
            # 尝试加载模型
            try:
                self.model = YOLO("yolov8n.pt")  # 使用预训练的YOLOv11模型
                # 强制切换到CUDA设备
                if torch.cuda.is_available():
                    self.model.to('cuda')
                    print("YOLO模型已切换到 CUDA 设备:", next(self.model.model.parameters()).device)
                else:
                    print("警告：未检测到可用的CUDA设备，YOLO将使用CPU运行。")
                print("YOLO模型加载成功")
            except Exception as e:
                print(f"加载YOLO模型出错: {e}")
                print("部分功能可能不可用")
        else:
            print("YOLO模块不可用，人体检测和水杯检测功能将不可用")
    
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
                    'annotated_frame': 带有检测框的帧
                }
        """
        annotated_frame = frame.copy()
        
        if self.model is None:
            return self.result
        
        try:
            yolo_result = self.model(frame)[0]  # 一张图片只有一个结果

            for box in yolo_result.boxes:
                cls = int(box.cls[0])
                if cls == 0:  # person
                    self.result['person_detected'] = True
                if cls == 41:  # cup
                    self.result['cup_detected'] = True

                # 为所有检测到的对象绘制边界框
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = f"{self.model.names[cls_id]} {conf:.2f}"
                
                # 绘制边界框
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 绘制标签背景
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 5), 
                                (x1 + label_size[0], y1), (0, 255, 0), -1)
                
                # 绘制标签文本
                cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            self.result['annotated_frame'] = annotated_frame
        except Exception as e:
            print(f"YOLO检测出错: {e}")
            traceback.print_exc()
            
        return self.result
