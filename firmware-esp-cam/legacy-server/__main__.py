import asyncio
from calendar import c
from matplotlib.pylab import f
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

latest_frame = None
last_frame_time = 0

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
    global latest_frame, last_frame_time, running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(0.001)  # 使用超时而不是非阻塞

    print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

    # 预分配缓冲区
    frame_buffer = defaultdict(dict)  # frame_id -> {chunk_id: bytes}
    frame_chunk_count = {}           # frame_id -> chunk_total
    CHUNK_LENGTH = 1472
    while running:
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)

            # 解析数据包头
            frame_index = int.from_bytes(data[0:4], 'little')
            chunk_index = int.from_bytes(data[4:6], 'little')
            chunk_total = int.from_bytes(data[6:8], 'little')
            chunk_payload = data[8:]

            print(
                f"Frame {frame_index}, Chunk {chunk_index}/{chunk_total}, Payload size: {len(chunk_payload)} bytes")

            # 存入缓存（可能乱序，所以直接放进 dict）
            frame_buffer[frame_index][chunk_index] = chunk_payload
            frame_chunk_count[frame_index] = chunk_total

            # 如果收齐了，立即组帧
            if chunk_total - len(frame_buffer[frame_index]) <= 0:
                chunks = [frame_buffer[frame_index][i]
                          for i in range(chunk_total) if i in frame_buffer[frame_index]]
                # 拼好帧
                latest_frame = b"".join(chunks)
                # 清理
                del frame_buffer[frame_index]
                del frame_chunk_count[frame_index]

                print(
                    f"JPEG frame complete, size: {len(latest_frame)} bytes, time: {time.time() - last_frame_time:.2f} seconds")
                last_frame_time = time.time()

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

        while True:
            if await request.is_disconnected():
                break

            # 检查是否有帧
            if latest_frame is None:
                await asyncio.sleep(0.01)  # 减少检查间隔
                continue

            yield (
                f"{boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(latest_frame)}\r\n\r\n"
            ).encode("utf-8") + latest_frame + b"\r\n"

            # 控制帧率，目标30FPS
            await asyncio.sleep(0.0333)

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# ...existing code...

if __name__ == "__main__":
    # 启动 UDP 监听线程
    uvicorn.run("legacy-server.__main__:app", host="0.0.0.0", port=8008)
