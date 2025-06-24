from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import cv2
import numpy as np


@dataclass
class DetectionBox:
    """单个检测框的信息"""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str
    extra_info: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yolo_box(cls, yolo_box, model_names: Dict[int, str]):
        """从 YOLO box 创建 DetectionBox"""
        x1, y1, x2, y2 = yolo_box.xyxy[0].cpu().numpy().astype(int)
        confidence = float(yolo_box.conf[0])
        class_id = int(yolo_box.cls[0])
        class_name = model_names.get(class_id, f"class_{class_id}")

        return cls(
            x1=x1, y1=y1, x2=x2, y2=y2,
            confidence=confidence,
            class_id=class_id,
            class_name=class_name
        )


@dataclass
class BaseDetectionResult:
    """检测结果基类（其他信息会被各个 detector 组合）"""
    boxes: List[DetectionBox] = field(default_factory=list)

    def get_boxes_by_class(self, class_name: str) -> List[DetectionBox]:
        return [box for box in self.boxes if box.class_name == class_name]

    def has_class(self, class_name: str) -> bool:
        return len(self.get_boxes_by_class(class_name)) > 0

    def draw_boxes_on(self, frame: np.ndarray, color=(0, 255, 0)) -> np.ndarray:
        """在帧上绘制检测框"""
        for box in self.boxes:
            # 绘制边界框
            cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), color, 2)

            # 绘制标签
            label = f"{box.class_name} {box.confidence:.2f}"
            label_size = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, (box.x1, box.y1 - label_size[1] - 5),
                          (box.x1 + label_size[0], box.y1), color, -1)
            cv2.putText(frame, label, (box.x1, box.y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return frame
