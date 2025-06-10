import threading
from typing import Dict, Optional
from .monitor import Monitor
from .camera_capture import create_camera_capture


class MonitorRegistry:
    """管理多个摄像头的Monitor实例"""

    def __init__(self):
        """初始化监控注册表"""
        # video_url -> Monitor实例
        self.monitors: Dict[str, Monitor] = {}

    def register(self, video_url: str):
        """注册摄像头"""
        for existing_url in self.monitors.keys():
            if existing_url == video_url:
                print(f"摄像头 {video_url} 已经注册，跳过重复注册")
                return
        # 创建新的Monitor实例
        self.monitors[video_url] = Monitor(video_url=video_url)
        return self # 供链式调用

    def start_all(self):
        """启动所有Monitor"""
        for monitor in self.monitors.values():
            monitor.start()

    def stop_all(self):
        """停止所有Monitor"""
        for monitor in self.monitors.values():
            monitor.stop()
