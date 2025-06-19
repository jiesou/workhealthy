from ast import Dict
from collections import defaultdict
from turtle import update
from . import BaseCameraCapture

import socket
import cv2
import time
import threading
import asyncio
import numpy as np

class UdpCameraCapture(BaseCameraCapture):
    """
    作为 UDP Server 管理每个 UDP 摄像头客户端（每个客户端都是独立实例）
    """
    MAX_PACKET_SIZE = 1472
    _udp_servers = {}  # (ip, port) -> server_info

    def __init__(self):
        super().__init__()
        # 存储所有摄像头捕获实例： addr, 'UdpCameraCapture'
        self.udp_ip: str = None
        self.udp_port: int = None
        self.camera_ip: str = None

    def start(self, video_url):
        # 添加新的摄像头捕获实例
        # url 格式 udpserver://0.0.0.0:8099/192.168.1.100
        if not video_url.startswith("udpserver://"):
            raise ValueError("[UdpCamera] video_url 必须以'udpserver://'开头")
        url = video_url[len("udpserver://"):]
        try:
            addr_part, self.camera_ip = url.split('/', 1)
            udp_server_ip, udp_server_port = addr_part.split(':')
            self.udp_ip = udp_server_ip
            self.udp_port = int(udp_server_port)
        except ValueError:
            raise ValueError(
                "[UdpCamera] video_url 格式错误，应为 udpserver://ip:port/camera_addr")
        
        server_key = (self.udp_ip, self.udp_port)
        print(f"[UdpCamera] 启动UDP服务器: {self.udp_ip}:{self.udp_port}，摄像头IP: {self.camera_ip}")
        if server_key not in self._udp_servers:
            # 创建新的服务器信息
            self._udp_servers[server_key] = {
                'udp_camera_clients': {},
                'is_running': False,
                'thread': None,
                'loop': None
            }
        
        # 添加当前摄像头客户端
        server_info = self._udp_servers[server_key]
        if self.camera_ip not in server_info['udp_camera_clients']:
            server_info['udp_camera_clients'][self.camera_ip] = UdpCameraClient(update_frame_callback=self._update_frame)
        # 启动UDP服务器（如果还没启动）
        if not server_info['is_running']:
            server_info['is_running'] = True
            self.is_running = True
            
            def run_loop():
                server_info['loop'] = asyncio.new_event_loop()
                asyncio.set_event_loop(server_info['loop'])
                server_info['loop'].run_until_complete(self._udp_listener(server_key))
            
            server_info['thread'] = threading.Thread(target=run_loop, daemon=True)
            server_info['thread'].start()
        
        print(f"[UdpCamera] server_info: {server_info}")

    def stop(self):
        self.is_running = False
        self.connected = False

        server_key = (self.udp_ip, self.udp_port)
        if server_key in self._udp_servers:
            server_info = self._udp_servers[server_key]
            # 移除当前摄像头客户端
            if self.camera_ip in server_info['udp_camera_clients']:
                del server_info['udp_camera_clients'][self.camera_ip]

            # 如果没有客户端了，停止服务器
            if not server_info['udp_camera_clients']:
                server_info['is_running'] = False
                del self._udp_servers[server_key]

    async def _udp_listener(self, server_key):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.udp_ip, self.udp_port))
        sock.setblocking(False)

        print(
            f"[UdpCamera] UDP server listening on {self.udp_ip}:{self.udp_port}")

        server_info = self._udp_servers[server_key]

        while server_info['is_running']:
            try:
                data, addr = sock.recvfrom(self.MAX_PACKET_SIZE)
                camera_ip = addr[0]
                if camera_ip in server_info['udp_camera_clients']:
                    server_info['udp_camera_clients'][camera_ip].process(data)
                else:
                    print(f"[UdpCamera] 未注册的摄像头连接: {camera_ip}")

            except BlockingIOError:
                await asyncio.sleep(0.001)
            except Exception as e:
                print(f"[UdpCamera] UDP监听错误: {e}")
                await asyncio.sleep(0.01)

        sock.close()

class UdpCameraClient():
    """
    处理摄像头发过来的 UDP 包，接收JPEG分片并组装完整帧
    """
    def __init__(self, update_frame_callback: callable):
        super().__init__()
        self.update_frame_callback = update_frame_callback
        self.frame_buffer = defaultdict(dict)  # frame_id -> {chunk_id: bytes}
        self.frame_chunk_count = {}            # frame_id -> chunk_total

    def process(self, data):
        if len(data) < 8:
            return  # 包头不足，丢弃

        # 解析包头
        frame_index = int.from_bytes(data[0:4], 'little')
        chunk_index = int.from_bytes(data[4:6], 'little')
        chunk_total = int.from_bytes(data[6:8], 'little')
        chunk_payload = data[8:]

        # 存入缓存（可能乱序，所以直接放进 dict）
        self.frame_buffer[frame_index][chunk_index] = chunk_payload
        self.frame_chunk_count[frame_index] = chunk_total

        self.cleanup_buffer()

        print(f"[UdpCamera] 收到分片: frame_index={frame_index}, chunk_index={chunk_index}, chunk_total={chunk_total}")

        # 如果收齐了，立即组帧
        if chunk_total - len(self.frame_buffer[frame_index]) <= 0:
            try:
                chunks = [self.frame_buffer[frame_index][i]
                            for i in range(chunk_total)]
            except KeyError:
                # 有分片丢失，跳过
                del self.frame_buffer[frame_index]
                del self.frame_chunk_count[frame_index]
                return

            latest_frame = b"".join(chunks)
            # 解码JPEG为OpenCV帧
            nparr = np.frombuffer(latest_frame, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                self.update_frame_callback(frame)
            else:
                print("[UdpCamera] JPEG解码失败")

            # 清理对应缓存
            del self.frame_buffer[frame_index]
            del self.frame_chunk_count[frame_index]

    def cleanup_buffer(self):
        """清理 buffer"""
        # 只保留最近5帧的buffer，防止内存泄漏
        while len(self.frame_buffer) > 5:
            key = next(iter(self.frame_buffer))
            self.frame_buffer.pop(key, None)
            self.frame_chunk_count.pop(key, None)
