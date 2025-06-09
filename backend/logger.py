import os
import time
from datetime import datetime
import threading

class ActivityLogger:
    """活动检测日志记录类"""
    
    def __init__(self, log_dir=None):
        """初始化日志记录器"""
        if log_dir is None:
            log_dir = os.path.dirname(__file__)
            
        self.activity_log_file_path = os.path.join(log_dir, "activity_detection.log")
        self.timing_log_file_path = os.path.join(log_dir, "detection_timing.log")
        self.log_lock = threading.Lock()
        
        # 用于构建日志条目的字典
        self.current_log_entry = {}
    
    def log_activity(self, frame_id, diff_ratio, is_active):
        """
        记录活动检测信息
        
        参数:
            frame_id: 帧ID
            diff_ratio: 帧差异比例
            is_active: 是否有活动
        """
        log_line = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] "
            f"frame_id={frame_id} diff_ratio={diff_ratio:.2f} is_active={is_active}\n"
        )
        with self.log_lock:
            with open(self.activity_log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
    
    def timing(self, key, value):
        """
        设置时间日志条目中的字段
        参数:
            key: 字段名
            value: 字段值
        返回:
            self: 支持链式调用
        """
        self.current_log_entry[key] = value
        return self
    
    def push(self, verbose=False):
        """
        提交当前时间日志条目到文件
        参数:
            verbose: 是否记录详细信息
        返回:
            self: 支持链式调用
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        if not verbose:
            log_line = (
                f"[{timestamp}] "
                f"frame_id={self.current_log_entry.get('frame_id', -1)} "
                f"fetch={self.current_log_entry.get('fetch', -1)}ms "
                f"yolo={self.current_log_entry.get('yolo', -1)}ms "
                f"total={self.current_log_entry.get('total', -1)}ms\n"
            )
        else:
            # 构建详细日志，包括所有设置的字段
            parts = [f"[{timestamp}]"]
            
            # 添加所有字段
            for key, value in self.current_log_entry.items():
                    parts.append(f"{key}={value}")
            
            log_line = " ".join(parts) + "\n"
        
        with self.log_lock:
            with open(self.timing_log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
        
        # 重置当前日志条目
        self.current_log_entry = {}
        
        return self
