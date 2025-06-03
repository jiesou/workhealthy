from collections import defaultdict
from . import BaseCameraCapture

import socket
import cv2
import time
import threading
import asyncio
import numpy as np


class UdpCameraCapture(BaseCameraCapture):
    """
    作为 UDP Server ，从UDP端口监听摄像头发过来的 UDP 包，接收JPEG分片并组装完整帧
    """

    def __init__(self):
        super().__init__()
        self.udp_ip = None
        self.udp_port = None
        self.chunk_length = 1023
        self.thread = None
        self.loop = None

    async def _udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.udp_ip, self.udp_port))
        sock.setblocking(False)

        print(
            f"[UdpCamera] UDP server listening on {self.udp_ip}:{self.udp_port}")

        frame_buffer = defaultdict(dict)  # frame_id -> {chunk_id: bytes}
        frame_chunk_count = {}            # frame_id -> chunk_total
        last_frame_time = time.time()
        MAX_PACKET_SIZE = 1472

        while self.is_running:
            try:
                data, addr = sock.recvfrom(MAX_PACKET_SIZE)
                if len(data) < 8:
                    continue  # 包头不足，丢弃

                # 解析包头
                frame_index = int.from_bytes(data[0:4], 'little')
                chunk_index = int.from_bytes(data[4:6], 'little')
                chunk_total = int.from_bytes(data[6:8], 'little')
                chunk_payload = data[8:]

                # 存入缓存（可能乱序，所以直接放进 dict）
                frame_buffer[frame_index][chunk_index] = chunk_payload
                frame_chunk_count[frame_index] = chunk_total

                # 如果收齐了，立即组帧
                if chunk_total - len(frame_buffer[frame_index]) <= 0:
                    try:
                        chunks = [frame_buffer[frame_index][i]
                                  for i in range(chunk_total)]
                    except KeyError:
                        # 有分片丢失，跳过
                        del frame_buffer[frame_index]
                        del frame_chunk_count[frame_index]
                        continue

                    latest_frame = b"".join(chunks)
                    # 解码JPEG为OpenCV帧
                    nparr = np.frombuffer(latest_frame, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        self._update_frame(frame)
                        self.connected = True
                        print(
                            f"[UdpCamera] 完整JPEG帧, 大小: {len(latest_frame)} bytes, 间隔: {time.time() - last_frame_time:.2f}s")
                        last_frame_time = time.time()
                    else:
                        print("[UdpCamera] JPEG解码失败")

                    # 清理缓存
                    del frame_buffer[frame_index]
                    del frame_chunk_count[frame_index]

            except BlockingIOError:
                await asyncio.sleep(0.001)
            except Exception as e:
                print(f"[UdpCamera] UDP监听错误: {e}")
                await asyncio.sleep(0.01)

        sock.close()
        self.connected = False

    def start(self, video_url):
        # 去掉前缀 udpserver://
        if video_url.startswith("udpserver://"):
            url = video_url[len("udpserver://"):]
        else:
            raise ValueError("[UdpCamera] video_url 必须以'udpserver://'开头")
        self.udp_ip, self.udp_port = url.split(':')
        self.udp_port = int(self.udp_port)
        """启动UDP监听线程"""
        if not self.is_running:
            self.is_running = True
            self.connected = False
            # 启动独立线程运行异步事件循环

            def run_loop():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(self._udp_listener())
            self.thread = threading.Thread(target=run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        """停止UDP监听"""
        self.is_running = False
        self.connected = False
        if hasattr(self, 'thread') and self.thread:
            self.thread.join(timeout=5)
