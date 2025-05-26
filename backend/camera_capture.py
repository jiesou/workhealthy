import asyncio
from socket import timeout
import websockets
import cv2
import numpy as np
import threading
import os


class CameraCapture:
    """
    WebSocket 视频客户端，替代 cv2.VideoCapture，兼容其接口。
    得到 ESP32-CAM 通过 WebSocket 发送的二进制 JPEG 数据
    """

    def __init__(self):
        self.cam_ws_url = os.getenv("CAM_WS_URL", "ws://192.168.10.100/ws")
        self.latest_frame = None
        self.is_running = False
        self.frame_lock = threading.Lock()  # 保护最新帧边界完整，必须使用锁
        self.connected = False

        self.start()

    async def _connect_and_receive(self):
        """连接 WebSocket 并接收视频帧"""
        while self.is_running:
            try:
                print(f"[CameraCapture] 尝试连接ESP32-CAM: {self.cam_ws_url}")
                async with websockets.connect(self.cam_ws_url, ping_timeout=1) as websocket:
                    print("[CameraCapture] 已连接到ESP32-CAM")
                    self.connected = True

                    async for message in websocket:
                        if not self.is_running:
                            break

                        assert (isinstance(message, bytes)
                                ), "CameraCapture 接收到非字节消息"
                        # ESP32-CAM发送的是二进制JPEG数据
                        frame = self._parse_frame(message)
                        with self.frame_lock:
                            print(f"[CameraCapture] 接收到新帧: {frame.shape if frame is not None else 'None'}")
                            self.latest_frame = frame

            except Exception as e:
                print(f"[CameraCapture] ESP32-CAM连接错误: {e}")
                self.connected = False
                if self.is_running:
                    await asyncio.sleep(1)  # 等待后重试

    def _parse_frame(self, message):
        """解析接收到的帧数据 - 直接解码 JPEG 字节"""
        try:
            # 直接从字节数据解码 JPEG
            nparr = np.frombuffer(message, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            print(f"[CameraCapture] 解析帧数据失败: {e}")
            return None

    """
    1. 为什么不直接 asyncio？
    cv2.VideoCapture 不是 async 的，如果整个 CameraCapture 写成 async 的，其他代码改动会很大。

    2. 那为什么不直接 threading？
    websockets 客户端库是 async 的。
    """

    def start(self):
        """启动 WebSocket 客户端，在线程中运行异步事件循环"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(
                target=lambda: asyncio.run(self._connect_and_receive()), daemon=True)
            self.thread.start()

    def release(self):
        self.is_running = False
        self.connected = False
        if hasattr(self, 'thread'):
            self.thread.join()

    def read(self):
        # 节流：每次读取间隔至少100ms（10fps）
        if not hasattr(self, '_last_read_time'):
            self._last_read_time = 0
        now = cv2.getTickCount() / cv2.getTickFrequency()
        elapsed = now - self._last_read_time
        if elapsed < 0.1:
            # 阻塞直到100ms过去
            to_sleep = 0.1 - elapsed
            if to_sleep > 0:
                threading.Event().wait(to_sleep)
        self._last_read_time = cv2.getTickCount() / cv2.getTickFrequency()

        with self.frame_lock:
            print("[CameraCapture] 读取最新帧", self.latest_frame.shape if self.latest_frame is not None else 'None')
            if self.latest_frame is not None:
                return True, self.latest_frame.copy()
            return False, None

    def isOpened(self):
        return self.is_running and self.connected

    def set(self, prop, value):
        """兼容 cv2.VideoCapture.set() 接口，但对 WebSocket 无效，直接 pass"""
        pass

# 单例，因为 VideoProcessor 里的错误处理会重新创建 cap
cameraCapture = CameraCapture()