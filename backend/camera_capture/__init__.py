import re
import time
from matplotlib.pylab import f
import numpy as np
import threading
from abc import ABC, abstractmethod


class BaseCameraCapture(ABC):
    """摄像头捕获基类，定义统一接口"""

    def __init__(self):
        # (height, width, 3), BGR格式
        self.latest_frame: np.ndarray | None = None
        self.latest_frame_time = None
        self.is_running = False
        self.connected = False
        self.frame_lock = threading.Lock()

    @abstractmethod
    def start(self, video_url: str):
        """启动摄像头捕获"""
        pass

    @abstractmethod
    def stop(self):
        """停止摄像头捕获"""
        pass

    def get_latest_frame(self) -> tuple[np.ndarray | None, float | None]:
        """获取最新帧（线程安全）"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy(), self.latest_frame_time
            return None, None

    def is_connected(self):
        """检查是否连接"""
        return self.is_running and self.connected

    def _update_frame(self, frame):
        """更新最新帧（内部方法，线程安全）"""
        with self.frame_lock:
            self.latest_frame = frame
            self.latest_frame_time = time.time()

# fmt: off
from .websocket import WebSocketCameraCapture
from .udpserver import UdpCameraCapture
from .cv2cam import CV2CameraCapture
# fmt: on


def create_camera_capture(video_url: str) -> BaseCameraCapture:
    """工厂函数：根据URL创建合适的摄像头捕获实例，兼容各种传输方式"""
    if video_url.startswith("ws://") or video_url.startswith("wss://"):
        return WebSocketCameraCapture()
    elif video_url.startswith("udpserver://"):
        return UdpCameraCapture()
    else:
        return CV2CameraCapture()
