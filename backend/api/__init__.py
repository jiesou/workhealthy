import signal
import threading
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("[Lifespan] 应用启动中...")

    yield  # 应用运行期间

    # 关闭时执行
    print("[Lifespan] 应用关闭中...")
    os.kill(os.getpid(), signal.SIGTERM)

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
    """获取所有监视终端列表"""
    return {
        "monitors": monitor_registry.monitors.keys(),
    }

app.include_router(monitor_router)

