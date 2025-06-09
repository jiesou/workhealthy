from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime, timedelta
import io
import os
from contextlib import asynccontextmanager
import face_recognition
import pickle
from ultralytics import YOLO

from database import crud, get_db
from .health_monitor import HealthMonitor

# 存储所有连接的客户端
connected_clients: set[WebSocket] = set()

ENCODINGS_PATH = "backend/facedata_encodings.pkl"

# 全局变量：已知人脸特征和姓名
KNOWN_ENCODINGS = []
KNOWN_NAMES = []

# 单独为刷脸签到加载 best.pt
BEST_MODEL_PATH = "backend/best.pt"
best_yolo_model = YOLO(BEST_MODEL_PATH)


def load_facedata():
    """加载人脸库特征到内存，支持特征缓存"""
    if os.path.exists(ENCODINGS_PATH):
        with open(ENCODINGS_PATH, "rb") as f:
            return pickle.load(f)
    encodings = []
    names = []
    facedata_dir = "backend/facedata"
    for filename in os.listdir(facedata_dir):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(facedata_dir, filename)
            img = face_recognition.load_image_file(img_path)
            feats = face_recognition.face_encodings(img)
            if feats:
                encodings.append(feats[0])
                names.append(name)
    # 保存特征缓存
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump((encodings, names), f)
    return encodings, names


# 项目启动时加载一次人脸库
KNOWN_ENCODINGS, KNOWN_NAMES = load_facedata()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("应用启动中...")
    health_monitor.start()

    # 启动后台任务
    background_task = asyncio.create_task(push_status_updates())

    yield  # 应用运行期间

    # 关闭时执行
    print("应用关闭中...")
    background_task.cancel()
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    health_monitor.stop()

# 创建FastAPI应用
app = FastAPI(title="工位健康监测系统", lifespan=lifespan)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建健康监测服务
# 从环境变量获取视频URL
video_url = os.getenv("VIDEO_URL")
health_monitor = HealthMonitor(video_url)


@app.get("/")
async def root():
    """API根路径"""
    return {"message": "工位健康监测系统API"}


@app.get("/status")
async def get_status():
    """获取当前状态"""
    status = health_monitor.get_status()
    # 转换datetime对象为字符串
    for key, value in status.items():
        if isinstance(value, datetime):
            status[key] = value.isoformat()

    if "health_metrics" in status and status["health_metrics"]:
        if "timestamp" in status["health_metrics"] and isinstance(status["health_metrics"]["timestamp"], datetime):
            status["health_metrics"]["timestamp"] = status["health_metrics"]["timestamp"].isoformat()

    return status


@app.get("/video_feed")
async def video_feed():
    """向前端提供 mjpeg 视频流"""
    async def generate():
        while True:
            frame = health_monitor.video_processor.get_latest_frame()
            if frame is not None:
                # 转换为JPEG
                _, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            await asyncio.sleep(0.1)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/health_metrics")
async def get_health_metrics(days: int = 7, db: Session = Depends(get_db)):
    """获取健康指标历史数据"""
    metrics = crud.get_health_metrics_history(db, days)

    # 转换为JSON可序列化格式
    result = []
    for metric in metrics:
        result.append({
            "id": metric.id,
            "timestamp": metric.timestamp.isoformat(),
        })

    return result


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接，用于实时推送状态更新"""
    print(f"收到新的WebSocket连接: {websocket.client}")
    try:
        await websocket.accept()
        print(f"WebSocket连接已接受: {websocket.client}")
        connected_clients.add(websocket)
        print(f"当前连接的客户端数量: {len(connected_clients)}")

        # 立即发送一次当前状态
        status = health_monitor.get_status()

        # 转换datetime对象为字符串
        for key, value in status.items():
            if isinstance(value, datetime):
                status[key] = value.isoformat()

        if "health_metrics" in status and status["health_metrics"]:
            if "timestamp" in status["health_metrics"] and isinstance(status["health_metrics"]["timestamp"], datetime):
                status["health_metrics"]["timestamp"] = status["health_metrics"]["timestamp"].isoformat()

        # 发送欢迎消息
        await websocket.send_json({
            "type": "welcome",
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        })

        # 发送当前状态
        await websocket.send_json(status)

        while True:
            # 等待客户端消息（保持连接）
            try:
                data = await websocket.receive_text()
                print(f"收到WebSocket消息: {data[:20]}...")
                json_data = json.loads(data)
                if "action" in json_data:
                    action = json_data["action"]
                    if action == "refresh_generator_summary_health":
                        health_monitor.refresh_generator_summary_health()
            except json.JSONDecodeError:
                print(f"WebSocket收到无效的JSON数据: {data[:20]}...")
            except WebSocketDisconnect:
                print(f"WebSocket连接断开: {websocket.client}")
                if websocket in connected_clients:
                    connected_clients.remove(websocket)
                break
            except Exception as e:
                print(f"WebSocket错误: {str(e)}")
    except WebSocketDisconnect:
        print(f"WebSocket连接断开: {websocket.client}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

# 后台任务：定期向所有连接的客户端推送状态更新


async def push_status_updates():
    """定期向所有WebSocket客户端推送状态更新"""
    while True:
        try:
            if connected_clients:
                status = health_monitor.get_status()
                print(f"推送状态更新: {status}")

                # 转换datetime对象为字符串
                for key, value in status.items():
                    if isinstance(value, datetime):
                        status[key] = value.isoformat()

                if "health_metrics" in status and status["health_metrics"]:
                    if "timestamp" in status["health_metrics"] and isinstance(status["health_metrics"]["timestamp"], datetime):
                        status["health_metrics"]["timestamp"] = status["health_metrics"]["timestamp"].isoformat()

                # 向所有连接的客户端发送状态更新
                disconnected_clients = set()
                for client in connected_clients:
                    try:
                        await client.send_json(status)
                    except Exception as e:
                        print(f"向客户端发送数据失败: {str(e)}")
                        disconnected_clients.add(client)

                # 移除断开连接的客户端
                for client in disconnected_clients:
                    if client in connected_clients:
                        connected_clients.remove(client)
                        print(f"移除断开的客户端，当前连接数: {len(connected_clients)}")
        except Exception as e:
            print(f"推送状态更新时出错: {str(e)}")

        # 每秒更新一次
        await asyncio.sleep(0.5)


@app.get("/video_status")
async def video_status():
    """检查视频流连接状态"""
    status = {
        "video_url": health_monitor.video_processor.video_url,
        "connected": False,
        "last_frame_time": None,
        "error": None
    }

    # 检查是否有最新帧
    frame = health_monitor.video_processor.get_latest_frame()
    if frame is not None:
        status["connected"] = True
        if health_monitor.video_processor.last_frame_time:
            status["last_frame_time"] = health_monitor.video_processor.last_frame_time.isoformat()
    else:
        status["error"] = "未获取到视频帧"

    # 输出到控制台
    if status["connected"]:
        print(f"视频流连接状态: 已连接 - {status['video_url']}")
    else:
        print(f"视频流连接状态: 未连接 - {status['video_url']} - 错误: {status['error']}")

    return status


@app.get("/toggle_yolo/{enable}")
async def toggle_yolo(enable: bool):
    """启用或禁用YOLO分析处理"""
    try:
        result = health_monitor.video_processor.set_yolo_processing(enable)
        action = "启用" if enable else "禁用"
        print(f"已{action} YOLO处理")
        return result
    except Exception as e:
        print(f"切换YOLO处理状态出错: {str(e)}")
        return {"status": "error", "message": str(e)}


def detect_hat_with_yolo(image_path, yolo_model):
    """用YOLO模型检测图片中是否有安全帽（类别名为'hat'）"""
    import cv2
    img = cv2.imread(image_path)
    results = yolo_model(img)
    for result in results:
        for box in result.boxes:
            cls_idx = int(box.cls[0])
            # 检查类别名是否为 'hat'
            if hasattr(yolo_model, 'names'):
                if yolo_model.names[cls_idx] == 'Hardhat':
                    return True
    return False


@app.post("/face_signin")
@app.post("/api/face_signin")
async def face_signin(image: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    刷脸签到接口：接收前端上传图片，做人脸识别，检测安全帽，保存签到记录
    """
    # 1. 保存上传图片
    images_dir = "backend/signin_images"
    os.makedirs(images_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    image_path = os.path.join(images_dir, f"signin_{timestamp}.jpg")
    with open(image_path, "wb") as f:
        f.write(await image.read())

    # 2. 直接用内存中的人脸特征
    if not KNOWN_ENCODINGS:
        result = "人脸库为空，无法识别"
        crud.create_signin_record(
            db, name=None, image_path=image_path, result=result)
        return {"success": False, "message": result}

    # 3. 识别上传图片
    unknown_img = face_recognition.load_image_file(image_path)
    unknown_encodings = face_recognition.face_encodings(unknown_img)
    if not unknown_encodings:
        result = "未检测到人脸"
        crud.create_signin_record(
            db, name=None, image_path=image_path, result=result)
        return {"success": False, "message": result}
    unknown_encoding = unknown_encodings[0]

    # 计算所有已知人脸的距离
    distances = face_recognition.face_distance(
        KNOWN_ENCODINGS, unknown_encoding)
    min_distance = float(distances.min())
    min_index = int(distances.argmin())

    # 设置更严格的阈值
    THRESHOLD = 0.4
    if min_distance < THRESHOLD:
        name = KNOWN_NAMES[min_index]
        # 4. 检测安全帽，使用best.pt模型
        if best_yolo_model is not None:
            has_hat = detect_hat_with_yolo(image_path, best_yolo_model)
            if not has_hat:
                result = "签到失败，请携带安全设备上岗"
                crud.create_signin_record(
                    db, name=name, image_path=image_path, result=result)
                return {"success": False, "message": result, "name": name, "distance": min_distance}
        result = f"欢迎，{name}！签到成功"
        crud.create_signin_record(
            db, name=name, image_path=image_path, result=result)
        return {"success": True, "message": result, "name": name, "distance": min_distance}
    else:
        result = "未识别到已注册人脸"
        crud.create_signin_record(
            db, name=None, image_path=image_path, result=result)
        return {"success": False, "message": result, "distance": min_distance}
