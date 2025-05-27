import asyncio, uvicorn
import socket
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from collections import defaultdict
import time
import signal
import sys

app = FastAPI()

# UDP 接收参数
UDP_IP = "0.0.0.0"
UDP_PORT = 8099
MAX_PACKET_SIZE = 1472

# 图像缓存（frame_id -> [packet_index -> data]）
frame_cache = defaultdict(dict)
frame_packet_count = {}
latest_frame = None
latest_frame_time = 0

# 添加全局标志
running = True


def signal_handler(sig, frame):
    global running
    print('收到停止信号，正在关闭服务器...')
    running = False
    sys.exit(0)


# 在主程序开始前注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# 启动后台任务监听 UDP
@app.on_event("startup")
async def start_udp_server():
    asyncio.create_task(udp_listener())


async def udp_listener():
    global latest_frame, latest_frame_time, running
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

    byte_vector = bytearray()  # 用于累积 JPEG 数据
    CHUNK_LENGTH = 1023  # 根据你的需求调整

    while running:  # 改为检查 running 标志
        try:
            data, addr = sock.recvfrom(MAX_PACKET_SIZE)
            print(f"Received packet length: {len(data)}")

            # 检查是否是新的 JPEG 开始 (FF D8 FF)
            if (len(data) == CHUNK_LENGTH and
                len(data) >= 3 and
                data[0] == 0xFF and
                data[1] == 0xD8 and
                    data[2] == 0xFF):
                print("New JPEG frame detected")
                byte_vector.clear()

            # 将当前包的数据添加到累积缓冲区
            byte_vector.extend(data)

            # 检查是否是 JPEG 结束 (FF D9)
            if (len(data) != CHUNK_LENGTH and
                len(data) >= 2 and
                data[-2] == 0xFF and
                    data[-1] == 0xD9):

                # 更新全局变量
                latest_frame = bytes(byte_vector)
                print(f"JPEG frame complete, size: {len(byte_vector)} bytes, time: {time.time() - latest_frame_time:.2f} seconds")
                latest_frame_time = time.time()

                # 清空缓冲区为下一帧做准备
                byte_vector.clear()

        except socket.error:
            # 非阻塞 socket，没有数据时会抛出异常
            await asyncio.sleep(0.001)  # 短暂休眠避免 CPU 占用过高
        except Exception as e:
            print(f"UDP listener error: {e}")
            await asyncio.sleep(0.01)


# MJPEG 视频流接口
@app.get("/")
async def mjpeg_stream(request: Request):
    async def stream():
        boundary = "--frame"
        while True:
            if await request.is_disconnected():
                break

            if latest_frame is None:
                await asyncio.sleep(0.1)
                continue

            yield (
                f"{boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(latest_frame)}\r\n\r\n"
            ).encode("utf-8") + latest_frame + b"\r\n"
            await asyncio.sleep(0.01)  # 控制帧率

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # 启动 UDP 监听线程
    uvicorn.run("legacy-server.__main__:app", host="0.0.0.0", port=8008)
