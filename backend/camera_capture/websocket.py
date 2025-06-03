from . import BaseCameraCapture

import websockets, threading, asyncio, cv2
import numpy as np


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
