from . import BaseCameraCapture

import cv2, time, threading


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
            self.thread = threading.Thread(
                target=self._capture_loop, daemon=True)
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
