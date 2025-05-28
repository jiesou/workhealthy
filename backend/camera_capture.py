import asyncio
import time
import websockets
import cv2
import numpy as np
import threading
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from abc import ABC, abstractmethod
import queue


class BaseCameraCapture(ABC):
    """摄像头捕获基类，定义统一接口"""
    
    def __init__(self):
        self.latest_frame: np.ndarray | None = None  # (height, width, 3), BGR格式
        self.latest_frame_time = None
        self.is_running = False
        self.connected = False
        self.frame_lock = threading.Lock()
    
    @abstractmethod
    def start(self, video_url):
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


class WebSocketCameraCapture(BaseCameraCapture):
    """
    WebSocket 视频客户端，从ESP32-CAM通过WebSocket接收JPEG数据
    """

    def __init__(self):
        super().__init__()
        self.cam_ws_url = None
        self.websocket = None
        self.thread = None

    async def _connect_and_receive(self):
        """连接 WebSocket 并接收视频帧"""
        while self.is_running:
            try:
                print(f"[WebSocketCamera] 尝试连接ESP32-CAM: {self.cam_ws_url}")
                async with websockets.connect(self.cam_ws_url, ping_timeout=0.3) as websocket:
                    print("[WebSocketCamera] 已连接到ESP32-CAM")
                    self.connected = True

                    async for message in websocket:
                        if not self.is_running:
                            break
                        
                        if isinstance(message, bytes):
                            frame = self._parse_frame(message)
                            if frame is not None:
                                self._update_frame(frame)
                                print("[WebSocketCamera] 接收到新帧")
                        else:
                            print("[WebSocketCamera] 接收到非字节消息")
                            
            except websockets.exceptions.ConnectionClosed:
                print("[WebSocketCamera] WebSocket连接已关闭，尝试重新连接...")
                self.connected = False
            except Exception as e:
                print(f"[WebSocketCamera] 连接出错: {e}")
                self.connected = False
                await asyncio.sleep(1)

    def _parse_frame(self, message):
        """解析接收到的帧数据 - 直接解码 JPEG 字节"""
        try:
            # 直接从字节数据解码 JPEG
            nparr = np.frombuffer(message, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"[WebSocketCamera] 解析帧数据失败: {e}")
            return None

    def start(self, video_url):
        """启动 WebSocket 客户端，在线程中运行异步事件循环"""
        self.cam_ws_url = video_url
        if not self.is_running:
            self.is_running = True
            self.connected = False
            self.thread = threading.Thread(
                target=lambda: asyncio.run(self._connect_and_receive()), daemon=True)
            self.thread.start()

    def stop(self):
        """停止WebSocket连接"""
        self.is_running = False
        self.connected = False
        if hasattr(self, 'thread') and self.thread:
            self.thread.join(timeout=5)


class CV2CameraCapture(BaseCameraCapture):
    """
    OpenCV 摄像头捕获，用于本地摄像头或HTTP视频流
    """
    
    def __init__(self):
        super().__init__()
        # 设置OpenCV的错误处理
        # OpenCV 4.0+ 才有 setLogLevel，低版本没有
        try:
            cv2.setLogLevel(cv2.LOG_LEVEL_SILENT)
        except Exception as e:
            print("[DEBUG] OpenCV setLogLevel not available or failed:", e)
        self.cap = None
        self.thread = None
        self.video_url = None
    
    def _capture_loop(self):
        """摄像头捕获主循环"""
        failure_count = 0
        max_failures = 10
        
        while self.is_running:
            try:
                # 创建VideoCapture对象
                if self.cap is None:
                    print(f"[CV2Camera] 尝试打开摄像头: {self.video_url}")
                    self.cap = cv2.VideoCapture(self.video_url)
                    
                    # 设置缓冲区大小和超时
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                    self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
                    
                    if not self.cap.isOpened():
                        raise ValueError("[CV2Camera] 无法打开摄像头")
                    
                    print("[CV2Camera] 摄像头已连接")
                    self.connected = True
                    failure_count = 0
                
                # 读取帧
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self._update_frame(frame)
                    time.sleep(0.033)  # 约30fps
                else:
                    raise ValueError("[CV2Camera] 读取帧失败")
                    
            except Exception as e:
                print(f"[CV2Camera] 捕获帧出错: {e}")
                self.connected = False
                failure_count += 1
                
                # 清理并重试
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                if failure_count >= max_failures:
                    print(f"[CV2Camera] 连续失败{max_failures}次，停止重试")
                    break
                
                time.sleep(min(failure_count * 0.5, 5))  # 指数退避
    
    def start(self, video_url):
        """启动摄像头捕获"""
        self.video_url = video_url
        if not self.is_running:
            self.is_running = True
            self.connected = False
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
    
    def stop(self):
        """停止摄像头捕获"""
        self.is_running = False
        self.connected = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        if hasattr(self, 'thread') and self.thread:
            self.thread.join(timeout=5)


def create_camera_capture(video_url) -> BaseCameraCapture:
    """工厂函数：根据URL创建合适的摄像头捕获实例"""
    if video_url.startswith("ws://") or video_url.startswith("wss://"):
        return WebSocketCameraCapture()
    else:
        return CV2CameraCapture()
