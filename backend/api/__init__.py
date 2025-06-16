import time
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

# 路由
from .monitor import router as monitor_router
# from . import history as history_api # Removed
from .monitor import monitor_registry

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

    yield  # 应用运行期间

    # 关闭时执行
    print("应用关闭中...")

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


@app.get("/")
async def root():
    """API根路径"""
    return {"message": "工位健康监测系统API"}


@app.get("/monitors")
async def get_monitors():
    """获取所有监控器列表"""
    return {
        "monitors": monitor_registry.monitors.keys(),
    }

app.include_router(monitor_router)
# app.include_router(history_api.router) # Removed


# TODO: 专门实现签到，清理 Legacy Code
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
