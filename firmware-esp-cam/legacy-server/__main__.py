import asyncio, uvicorn
import socket
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from collections import defaultdict
import time

app = FastAPI()

# UDP 接收参数
UDP_IP = "0.0.0.0"
UDP_PORT = 8099
MAX_PACKET_SIZE = 1024

# 图像缓存（frame_id -> [packet_index -> data]）
frame_cache = defaultdict(dict)
frame_packet_count = {}
latest_frame = None
latest_frame_time = 0


# 启动后台任务监听 UDP
@app.on_event("startup")
async def start_udp_server():
    asyncio.create_task(udp_listener())


async def udp_listener():
    global latest_frame, latest_frame_time
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)

    print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

    while True:
        try:
            data, addr = sock.recvfrom(2048)
            if len(data) < 6:
                continue

            # 解码包头
            frame_id = (data[0] << 8) | data[1]
            packet_id = (data[2] << 8) | data[3]
            total_packets = (data[4] << 8) | data[5]
            payload = data[6:]

            frame_cache[frame_id][packet_id] = payload
            frame_packet_count[frame_id] = total_packets

            # 判断是否收全一帧
            if len(frame_cache[frame_id]) == total_packets:
                print(f"Received complete frame {frame_id} with {total_packets} packets")
                # 重新组装 JPEG 图像
                parts = [frame_cache[frame_id][i]
                         for i in range(total_packets)]
                full_frame = b''.join(parts)
                latest_frame = full_frame
                latest_frame_time = time.time()

                # 清理旧帧
                keys_to_delete = [
                    fid for fid in frame_cache if fid != frame_id]
                for k in keys_to_delete:
                    del frame_cache[k]
                    del frame_packet_count[k]

        except BlockingIOError:
            await asyncio.sleep(0.001)


# MJPEG 视频流接口
@app.get("/video")
async def mjpeg_stream(request: Request):
    async def stream():
        boundary = "--frame"
        while True:
            if await request.is_disconnected():
                break

            if latest_frame:
                yield (
                    f"{boundary}\r\n"
                    f"Content-Type: image/jpeg\r\n"
                    f"Content-Length: {len(latest_frame)}\r\n\r\n"
                ).encode("utf-8") + latest_frame + b"\r\n"
            await asyncio.sleep(0.05)  # 控制帧率

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # 启动 UDP 监听线程
    uvicorn.run("legacy-server.__main__:app", host="0.0.0.0", port=8008)
