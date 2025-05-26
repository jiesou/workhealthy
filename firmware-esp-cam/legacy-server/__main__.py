import asyncio
import base64
import json
from io import BytesIO
import face_recognition
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import websockets
from PIL import Image, ImageDraw
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 保存浏览器客户端连接
browser_clients = set()


@app.get("/")
async def get():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP-CAM Face Detection Stream</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                background-color: #f0f0f0;
                margin: 0;
                padding: 20px;
            }
            #img { 
                border: 2px solid #333; 
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                max-width: 90%;
            }
            .status {
                margin: 10px 0;
                font-size: 18px;
            }
            .connected { color: green; }
            .disconnected { color: red; }
        </style>
    </head>
    <body>
        <h1>ESP-CAM Face Detection Stream</h1>
        <div id="status" class="status disconnected">连接状态: 断开</div>
        <img id="img" src="" width="640px" alt="等待图像..."/>
        <script>
            const ws = new WebSocket("ws://" + location.host + "/ws/browser");
            const statusDiv = document.getElementById("status");
            
            ws.onopen = () => {
                statusDiv.textContent = "连接状态: 已连接";
                statusDiv.className = "status connected";
            };
            
            ws.onclose = () => {
                statusDiv.textContent = "连接状态: 断开";
                statusDiv.className = "status disconnected";
            };
            
            ws.onerror = () => {
                statusDiv.textContent = "连接状态: 错误";
                statusDiv.className = "status disconnected";
            };
            
            ws.onmessage = (event) => {
                document.getElementById("img").src = "data:image/jpeg;base64," + event.data;
            };
        </script>
    </body>
    </html>
    """)


@app.websocket("/ws/browser")
async def browser_websocket(websocket: WebSocket):
    await websocket.accept()
    browser_clients.add(websocket)
    logger.info(f"浏览器客户端连接，当前连接数: {len(browser_clients)}")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        browser_clients.discard(websocket)
        logger.info(f"浏览器客户端断开，当前连接数: {len(browser_clients)}")


def detect_and_draw_faces(image_data):
    """检测人脸并画框"""
    try:
        # 将图像数据转为PIL图像
        img = Image.open(BytesIO(image_data))
        rgb_img = np.array(img)

        # 检测人脸
        face_locations = face_recognition.face_locations(rgb_img)

        if face_locations:
            # 在原图上画框
            draw = ImageDraw.Draw(img)
            for (top, right, bottom, left) in face_locations:
                # 画绿色矩形框
                draw.rectangle([(left, top), (right, bottom)],
                               outline="green", width=3)
                # 添加标签
                draw.text((left, top-20), "Face", fill="green")

            # 转回字节
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            return output.getvalue()
        else:
            return image_data

    except Exception as e:
        logger.error(f"人脸检测错误: {e}")
        return image_data


async def broadcast_to_browsers(image_data):
    """广播图像到所有浏览器客户端"""
    if not browser_clients:
        return

    base64_img = base64.b64encode(image_data).decode("utf-8")
    disconnected = []

    for client in browser_clients:
        try:
            await client.send_text(base64_img)
        except:
            disconnected.append(client)

    for client in disconnected:
        browser_clients.discard(client)


async def connect_to_esp_cam():
    """连接到ESP32-CAM的WebSocket"""
    esp_cam_uri = "ws://192.168.10.100/ws"

    while True:
        try:
            logger.info(f"尝试连接ESP32-CAM: {esp_cam_uri}")
            async with websockets.connect(esp_cam_uri) as websocket:
                logger.info("已连接到ESP32-CAM")

                async for message in websocket:
                    # ESP32-CAM发送的是二进制JPEG数据
                    if isinstance(message, bytes):
                        start_time = asyncio.get_event_loop().time()
                        logger.info("接收到ESP32-CAM图像数据")
                        # 人脸检测并画框
                        processed_image = detect_and_draw_faces(message)
                        end_time = asyncio.get_event_loop().time()
                        logger.info(f"处理图像耗时: {end_time - start_time:.2f}秒")
                        
                        # 广播给浏览器客户端
                        await broadcast_to_browsers(processed_image)

        except Exception as e:
            logger.error(f"ESP32-CAM连接错误: {e}")
            await asyncio.sleep(5)  # 等待5秒后重试


@app.on_event("startup")
async def startup_event():
    """应用启动时创建后台任务"""
    asyncio.create_task(connect_to_esp_cam())


@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "browser_clients": len(browser_clients)
    }

if __name__ == "__main__":
    uvicorn.run("server.__main__:app", host="0.0.0.0", port=8080)
