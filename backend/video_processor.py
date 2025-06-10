from typing import TypedDict
import cv2
import numpy as np
import time
from datetime import datetime
import os
import threading
import traceback

from sympy import det
from torch import Type
# 导入摄像头捕获
from backend.camera_capture import create_camera_capture
# 导入YOLO检测器
from backend.yolo_detector import YoloDetector
# 导入日志记录器
from backend.logger import ActivityLogger


class VideoProcessor:
    """视频处理类，负责从摄像头获取视频流并进行分析"""

    class DetectionStatus():
        is_person_detected: bool = False
        person_detected_time: int = 0

        is_cup_detected: bool = False
        cup_detected_time: int = 0
        
        is_active: bool = False
        active_time: int = 0

    def __init__(self, video_url="http://localhost:8081/mjpeg"):
        """
        初始化视频处理器

        参数:
            video_url: 视频流URL或摄像头索引，默认使用本地摄像头（索引0）
        """
        self.video_url = video_url
        # 创建摄像头实例
        self.camera = create_camera_capture(video_url)
        self.camera.start(video_url)
        print(f"[VideoProcessor] 启动摄像头: {self.camera}")

        self.yolo_detector = YoloDetector()
        self.logger = ActivityLogger()

        self.status = VideoProcessor.DetectionStatus()

        # 帧相关变量
        self.frame_buffer = []
        self.frame_index = 0
        self.annotated_frame = None

        # 处理控制变量
        self.enable_yolo_processing = True

        # 启动视频处理线程"
        self.processing_thread = threading.Thread(
            target=self._process_video_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _process_video_loop(self):
        """处理视频流的主循环"""
        last_processing_time = 0
        while True:
            current_time_ms = int(time.time_ns() / 1_000_000)

            # 控制处理频率
            if current_time_ms - last_processing_time < 1.0 / 5:  # 每秒处理5帧
                time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
                continue

            last_processing_time = current_time_ms

            # 获取最新帧
            frame, latest_frame_time_ms = self.camera.get_latest_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            # 检查帧是否太旧
            frame_age = current_time_ms - \
                latest_frame_time_ms if latest_frame_time_ms else float('inf')
            if frame_age > 1000:  # 超过1秒的帧丢弃
                continue

            # 更新帧缓冲区
            self.frame_buffer.append(frame)
            if len(self.frame_buffer) > 30: # 保持缓冲区最多30帧，用于活动检测
                self.frame_buffer.pop(0)

            self.frame_index += 1

            # 分析当前帧
            self._analyze_frame(frame)

    def _analyze_frame(self, frame: np.ndarray):
        processing_start_time = time.time()

        # 创建开始时间记录 设置帧 index
        log_entry = self.logger.timing('frame_id', self.frame_index)

        # 如果启用了YOLO处理
        if self.enable_yolo_processing:
            try:
                yolo_start = time.time()
                # 使用YOLO检测器进行检测
                self.detection_result = self.yolo_detector.detect(frame)
                self.annotated_frame = self.detection_result['annotated_frame']

                self._update_person_status()
                self._update_cup_status()

                # 记录YOLO处理时间
                log_entry.timing('yolo', int(
                    (time.time() - yolo_start) * 1000))
            except Exception as e:
                print(f"[VideoProcessor] YOLO分析出错: {e}")
                e.with_traceback(traceback.format_exc())
                log_entry.timing('yolo', -1)
        else:
            # 只显示原始帧
            self.annotated_frame = frame.copy()
            log_entry.timing('yolo', 0)

        # 进行活动检测
        activity_start = time.time()
        self._update_activity_detect()
        log_entry.timing('activity', int(
            (time.time() - activity_start) * 1000))

        # 记录处理时间和状态
        processing_end_time = time.time()
        log_entry.timing('total', int((processing_end_time - processing_start_time) * 1000))
        # 记录检测状态
        log_entry.timing('status', self.status)
        # 提交日志
        log_entry.push(verbose=True)

    def _update_activity_detect(self):
        """检测员工是否有活动"""
        if len(self.frame_buffer) < 2:
            return

        prev_frame = cv2.cvtColor(self.frame_buffer[-2], cv2.COLOR_BGR2GRAY)
        curr_frame = cv2.cvtColor(self.frame_buffer[-1], cv2.COLOR_BGR2GRAY)

        frame_diff = cv2.absdiff(prev_frame, curr_frame)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)

        diff_ratio = np.sum(thresh) / \
            (thresh.shape[0] * thresh.shape[1] * 255) * 100

        current_time_ms = int(time.time_ns() / 1_000_000)
        
        if diff_ratio > 0.4:  # 如果差异比例大于阈值，认为有活动
            self.status.is_active = True
            self.status.active_time = current_time_ms
        else:
            # 如果已经有活动时间记录，并且间隔超过10秒，则认为静止
            if self.status.active_time > 0:
                inactivity_duration = (current_time_ms - self.status.active_time) / 1000
                if inactivity_duration > 10:  # 10秒无活动认为静止
                    self.status.is_active = False

        # 日志记录
        self.logger.log_activity(self.frame_index, diff_ratio, self.status.is_active)

    def _update_person_status(self):
        """更新人体检测状态"""
        current_time_ms = int(time.time_ns() / 1_000_000)
        
        if self.detection_result['person_detected']:
            self.status.is_person_detected = True
            self.status.person_detected_time = current_time_ms
        else:
            # 如果现在没有人，但之前检测到人，检查absence时间
            if self.status.is_person_detected and self.status.person_detected_time > 0:
                absence_duration = (current_time_ms - self.status.person_detected_time) / 1000
                if absence_duration > 2:  # 2秒后认为人离开
                    self.status.is_person_detected = False
            else:
                self.status.is_person_detected = False

    def _update_cup_status(self):
        """更新水杯检测状态"""
        current_time_ms = int(time.time_ns() / 1_000_000)
        
        if self.detection_result['cup_detected']:
            self.status.is_cup_detected = True
            self.status.cup_detected_time = current_time_ms
        else:
            # 如果之前检测到水杯，检查absence时间
            if self.status.is_cup_detected and self.status.cup_detected_time > 0:
                no_cup_duration = (current_time_ms - self.status.cup_detected_time) / 1000
                if no_cup_duration > 5:  # 5秒后认为没有水杯
                    self.status.is_cup_detected = False
            else:
                self.status.is_cup_detected = False

    def get_latest_frame(self):
        """获取最新的视频帧（用于前端显示，带有检测框）"""
        # 优先返回带有检测框的显示帧
        if self.annotated_frame is not None:
            return self.annotated_frame
        # 如果没有显示帧，则返回相机原始帧
        frame, _ = self.camera.get_latest_frame()
        return frame

    def set_yolo_processing(self, enable):
        """设置是否启用YOLO处理"""
        self.enable_yolo_processing = enable
