import cv2
import threading
import time
import numpy as np
from fastapi import FastAPI, Response
from starlette.responses import StreamingResponse
import asyncio
import argparse
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加CORS中间件，允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoCaptureAsync:
    """
    异步视频采集类，支持本地摄像头和网络流。
    采集线程持续更新最新帧，供异步接口高并发读取。
    """
    def __init__(self, source=0):
        self.source = source
        self.frame = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
            self.thread = None

    def _capture_loop(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            print(f"无法打开视频源: {self.source}")
            return
        while self.is_running:
            ret, frame = cap.read()
            if ret:
                with self.lock:
                    self.frame = frame.copy()
            time.sleep(0.01)  # 控制采集频率
        cap.release()

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

# 解析命令行参数，支持摄像头或网络流
parser = argparse.ArgumentParser(description="异步视频代理服务")
parser.add_argument("--source", default=0, help="视频源（摄像头索引或流URL）")
args, _ = parser.parse_known_args()

# 创建视频采集对象
video_capture = VideoCaptureAsync(args.source)

@app.on_event("startup")
def startup_event():
    """FastAPI启动时启动采集线程"""
    video_capture.start()
    print(f"视频采集线程已启动，源: {args.source}")

@app.on_event("shutdown")
def shutdown_event():
    """FastAPI关闭时停止采集线程"""
    video_capture.stop()
    print("视频采集线程已停止")

@app.get("/mjpeg")
async def mjpeg_stream():
    """
    MJPEG流接口，适合网页实时预览。
    支持高并发，互不阻塞。
    """
    async def gen():
        while True:
            frame = video_capture.get_frame()
            if frame is None:
                # 返回空白帧
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "无视频信号", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            await asyncio.sleep(0.05)  # 控制推流帧率
    return StreamingResponse(gen(), media_type='multipart/x-mixed-replace; boundary=frame')

@app.get("/frame")
async def single_frame():
    """
    单帧图片接口，适合后端AI分析或定时抓拍。
    """
    frame = video_capture.get_frame()
    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(frame, "无视频信号", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    _, jpeg = cv2.imencode('.jpg', frame)
    return Response(jpeg.tobytes(), media_type='image/jpeg')

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head><title>异步视频代理</title></head>
        <body>
            <h1>异步视频代理服务</h1>
            <ul>
                <li><a href="/mjpeg" target="_blank">MJPEG 流预览</a></li>
                <li><a href="/frame" target="_blank">单帧图片</a></li>
            </ul>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("video_proxy_async:app", host="0.0.0.0", port=8081, reload=False) 