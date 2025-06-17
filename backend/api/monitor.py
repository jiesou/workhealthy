import datetime
import time
from database import crud, get_db, models # Added models
import json
import asyncio
import cv2
from typing import List # Added List

import urllib.parse
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session # Added Session

from backend.monitor import Monitor
from backend.monitor_registry import MonitorRegistry

# 创建监控注册表
monitor_registry = MonitorRegistry()
monitor_registry.register("udpserver://0.0.0.0:8099/192.168.10.102")
monitor_registry.register("udpserver://0.0.0.0:8099/192.168.10.100")

# 存储所有连接的 WebSockets 客户端，按 video_url 分组
connected_clients: dict[str, set[WebSocket]] = {}

router = APIRouter(prefix="/monitor", tags=["monitor"])


def get_monitor(blur_video_url: str) -> tuple[str, Monitor]:
    """
    依赖注入函数：解析video_url并返回监控器实例
    返回 (resolved_url, monitor) 元组
    """

    blur_video_url = urllib.parse.unquote(blur_video_url)
    print(f"[/monitor/{blur_video_url}] 解析视频URL")

    # 首先检查直接匹配
    if blur_video_url in monitor_registry.monitors:
        monitor = monitor_registry.monitors[blur_video_url]
        return blur_video_url, monitor

    # 支持多个关键词模糊匹配（以逗号分隔）
    keywords = [kw.strip() for kw in blur_video_url.split(",") if kw.strip()]
    for existing_url in monitor_registry.monitors.keys():
        if all(kw in existing_url for kw in keywords):
            monitor = monitor_registry.monitors[existing_url]
            return existing_url, monitor

    # 如果没找到匹配的，抛出异常
    raise HTTPException(
        status_code=404, detail=f"Monitor not found")

@router.get("/list")
async def list_monitors():
    """获取所有监控器的列表"""
    return list(monitor_registry.monitors.keys())


@router.get("/{blur_video_url}/video_feed")
async def monitor_video_feed(monitor_info: tuple[str, Monitor] = Depends(get_monitor)):
    """指定监控器的视频流"""
    resolved_url, monitor = monitor_info

    async def generate():
        while True:
            frame = monitor.video_processor.get_latest_frame()
            if frame is not None:
                # 转换为JPEG
                _, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            await asyncio.sleep(0.1)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.websocket("/{blur_video_url}/ws")
async def websocket_monitor(websocket: WebSocket, blur_video_url: str):
    """指定监控器的WebSocket连接"""
    print(f"[/monitor/{blur_video_url}/ws] 收到新的 WebSocket 连接")

    # 手动解析URL（WebSocket不支持依赖注入）
    resolved_url, monitor = get_monitor(blur_video_url)

    if resolved_url not in connected_clients:
        connected_clients[resolved_url] = set()

    try:
        await websocket.accept()
        connected_clients[resolved_url].add(websocket)

        # 发送欢迎消息
        await websocket.send_json({
            "type": "welcome",
            "message": f"WebSocket连接已建立 - 监控器 {resolved_url}",
            "timestamp": time.time(),
            "camera_ip": resolved_url
        })

        while True:
            try:
                data = await websocket.receive_text()
                json_data = json.loads(data)
                if "action" in json_data:
                    action = json_data["action"]
                    if action == "refresh_generator_summary_health":
                        monitor = monitor_registry.monitors.get(resolved_url)
                        if monitor:
                            monitor.refresh_generator_summary_health()
            except json.JSONDecodeError:
                print(f"[/monitor/{resolved_url}/ws] 收到无效的JSON数据")
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[/monitor/{resolved_url}/ws] 错误: {str(e)}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[/monitor/{resolved_url}/ws] 错误: {str(e)}")
    finally:
        if websocket in connected_clients.get(resolved_url, set()):
            connected_clients[resolved_url].remove(websocket)

async def push_status_updates():
    """定期向所有WebSocket客户端推送状态更新"""
    while True:
        try:
            # 推送各客户端状态
            for video_url in list(connected_clients.keys()):
                if video_url not in monitor_registry.monitors:
                    raise Exception(f"Push {video_url} Monitor not found")
                # 找到这个客户端对应的监控器
                monitor = monitor_registry.monitors[video_url]

                # today_work_duration logic removed from here

                current_insights = monitor.output_insights() # This now contains the formatted messages
                status_payload = {
                    **current_insights, # Spread the insights dictionary
                    "timestamp": int(time.time()),
                    "camera_ip": video_url,
                    "person_detected": monitor.video_processor.status.is_person_detected,
                    "cup_detected": monitor.video_processor.status.is_cup_detected
                }

                clients_to_disconnect = set()
                for client in connected_clients[video_url]:
                    try:
                        await client.send_json(status_payload) # Use new status_payload
                    except Exception as e:
                        clients_to_disconnect.add(client)
                # 清理已断开的客户端
                connected_clients[video_url].difference_update(
                    clients_to_disconnect)
        except Exception as e:
            print(f"[/ws push] 推送状态更新时出错: {str(e)}")
        await asyncio.sleep(0.5)
asyncio.create_task(push_status_updates())


@router.get("/{blur_video_url}/toggle_yolo/{enable}")
async def toggle_yolo(enable: bool, monitor_info: tuple[str, Monitor] = Depends(get_monitor)):
    """启用或禁用YOLO分析处理"""
    resolved_url, monitor = monitor_info
    monitor.video_processor.enable_yolo_processing = enable
    return {"status": "success", "message": f"YOLO处理已{'启用' if enable else '禁用'}"}

@router.get("/{blur_video_url}/history") #, response_model=List[models.WorkingSession])
async def get_monitor_work_session_history(
    blur_video_url: str, # This will be handled by get_monitor dependency
    start_date_ts: int,
    end_date_ts: int,
    db: Session = Depends(get_db),
    monitor_info: tuple[str, Monitor] = Depends(get_monitor) # Use existing dependency
):
    resolved_url, monitor = monitor_info
    # resolved_url is the actual monitor_video_url needed for crud

    sessions = crud.get_work_sessions_for_period(
        db,
        monitor_video_url=resolved_url,
        start_date_ts=start_date_ts,
        end_date_ts=end_date_ts
    )
    return sessions
