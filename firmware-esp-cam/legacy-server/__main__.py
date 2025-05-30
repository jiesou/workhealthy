import asyncio
import uvicorn
import socket
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from collections import defaultdict
import time
import signal
import sys
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# UDP 接收参数
UDP_IP = "0.0.0.0"
UDP_PORT = 8099
MAX_PACKET_SIZE = 1472

# 图像缓存优化
latest_frame = None
latest_frame_time = 0
frame_lock = asyncio.Lock()

# 添加全局标志
running = True


def signal_handler(sig, frame):
    global running
    print('收到停止信号，正在关闭服务器...')
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 使用线程池处理UDP接收
executor = ThreadPoolExecutor(max_workers=1)


def udp_receiver():
    """在独立线程中运行UDP接收"""
    global latest_frame, latest_frame_time, running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.001)  # 使用超时而不是非阻塞

    print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

    # 预分配缓冲区
    byte_vector = bytearray(200000)  # 预分配足够大的空间
    current_size = 0
    CHUNK_LENGTH = 1023

    while running:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)

            # 检查是否是新的 JPEG 开始
            if (len(data) == CHUNK_LENGTH and
                len(data) >= 3 and
                data[0] == 0xFF and
                data[1] == 0xD8 and
                    data[2] == 0xFF):
                print("New JPEG frame detected")
                current_size = 0

            # 直接写入预分配的缓冲区
            if current_size + len(data) < len(byte_vector):
                byte_vector[current_size:current_size + len(data)] = data
                current_size += len(data)

            # 检查是否是 JPEG 结束
            if (len(data) != CHUNK_LENGTH and
                len(data) >= 2 and
                data[-2] == 0xFF and
                    data[-1] == 0xD9):

                # 复制完整帧数据
                frame_time = time.time()
                frame_data = bytes(byte_vector[:current_size])

                # 原子更新
                latest_frame = frame_data
                latest_frame_time = frame_time

                print(
                    f"JPEG frame complete, size: {current_size} bytes, time: {frame_time - latest_frame_time:.2f} seconds")
                current_size = 0

        except socket.timeout:
            continue
        except Exception as e:
            print(f"UDP receiver error: {e}")
            time.sleep(0.001)

    sock.close()


@app.on_event("startup")
async def start_udp_server():
    # 在独立线程中启动UDP接收
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, udp_receiver)

# 优化MJPEG流


@app.get("/")
async def mjpeg_stream(request: Request):
    async def stream():
        boundary = "--frame"
        last_frame_time = 0

        while True:
            if await request.is_disconnected():
                break

            # 检查是否有新帧
            if latest_frame is None or latest_frame_time <= last_frame_time:
                await asyncio.sleep(0.01)  # 减少检查间隔
                continue

            frame_data = latest_frame  # 获取当前帧
            last_frame_time = latest_frame_time

            yield (
                f"{boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame_data)}\r\n\r\n"
            ).encode("utf-8") + frame_data + b"\r\n"

            # 控制帧率，目标20FPS
            await asyncio.sleep(0.05)

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# ...existing code...

if __name__ == "__main__":
    # 启动 UDP 监听线程
    uvicorn.run("legacy-server.__main__:app", host="0.0.0.0", port=8008)
