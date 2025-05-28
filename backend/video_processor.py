import cv2
import numpy as np
import time
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image
import os
import threading
import traceback
# 导入摄像头捕获
from backend.camera_capture import create_camera_capture

# 在导入YOLO之前设置torch.load配置
try:
    import torch
    # 设置torch.load的weights_only参数为False，解决PyTorch 2.6兼容性问题
    _original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load
except ImportError:
    pass

# 导入YOLO
try:
    from ultralytics import YOLO
except ImportError:
    print("警告: 无法导入ultralytics，部分功能可能不可用")
    YOLO = None

class VideoProcessor:
    """视频处理类，负责从摄像头获取视频流并进行分析"""
    
    def __init__(self, video_url="http://localhost:8081/mjpeg"):
        """
        初始化视频处理器
        
        参数:
            video_url: 视频流URL或摄像头索引，默认使用本地摄像头（索引0）
        """
        self.video_url = video_url
        self.last_frame = None
        self.last_frame_time = None
        # 创建摄像头实例
        self.camera = create_camera_capture(video_url)
        
        self.is_running = False
        self.thread = None
        self.frame_buffer = []
        self.max_buffer_size = 30  # 存储30帧用于活动检测
        
        # 添加一个专用于前端显示的帧
        self.display_frame = None
        self.display_frame_time = None
        
        # 添加视频处理锁，防止同时读写冲突
        self.frame_lock = threading.Lock()
        
        # 添加帧处理标志，控制是否进行YOLO分析
        self.enable_yolo_processing = True
        
        self.last_process_time = time.time()
        # 新增：YOLO检测频率控制
        self.yolo_interval = 0.2  # YOLO检测最小间隔（秒）
        self.last_yolo_time = 0
        
        # 加载YOLO模型
        self.model = None
        if YOLO is not None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
            if not os.path.exists(os.path.dirname(model_path)):
                os.makedirs(os.path.dirname(model_path))
            
            # 尝试加载模型
            try:
                self.model = YOLO("yolov8n.pt")  # 使用预训练的YOLOv8模型
                # 强制切换到CUDA设备
                if torch.cuda.is_available():
                    self.model.to('cuda')
                    print("YOLO模型已切换到 CUDA 设备:", next(self.model.model.parameters()).device)
                else:
                    print("警告：未检测到可用的CUDA设备，YOLO将使用CPU运行。")
                print("YOLO模型加载成功")
            except Exception as e:
                print(f"加载YOLO模型出错: {e}")
                print("部分功能可能不可用")
        else:
            print("YOLO模块不可用，人体检测和水杯检测功能将不可用")
        
        # 人体检测相关变量
        self.person_detected = False
        self.last_person_detection_time = None
        self.person_absence_start_time = None
        
        # 活动检测相关变量
        self.is_active = False
        self.last_activity_time = None
        self.activity_threshold = 0.4  # 帧差异阈值，diff_ratio>0.4才认为有活动
        
        # 水杯检测相关变量
        self.cup_detected = False
        self.last_cup_detection_time = None
        
        # 帧ID计数器
        self.frame_id = 0
        # 日志文件路径
        self.log_file_path = os.path.join(os.path.dirname(__file__), "detection_timing.log")
        # 日志写入锁
        self.log_lock = threading.Lock()
        # 活动检测日志文件
        self.activity_log_file_path = os.path.join(os.path.dirname(__file__), "activity_detection.log")
    
    def start(self):
        """启动视频处理线程"""
        if not self.is_running:
            self.is_running = True
            # 启动处理线程
            self.thread = threading.Thread(target=self._process_video_stream)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """停止视频处理线程"""
        self.is_running = False
        # 停止摄像头
        self.camera.stop()
        if self.thread:
            self.thread.join()
    
    def _process_video_stream(self):
        """处理视频流的主循环"""
        # 处理频率控制：每秒5次处理
        processing_interval = 1.0 / 5
        last_processing_time = 0

        # 启动摄像头（只启动一次）
        self.camera.start(self.video_url)
        print(f"[VideoProcessor] 启动摄像头: {self.camera}")

        while self.is_running:
            current_time = time.time()

            if current_time - last_processing_time < processing_interval:
                time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
                continue

            frame, latest_frame_time = self.camera.get_latest_frame()
            if frame is None:
                # 没有帧可用，继续等待
                time.sleep(0.1)
                continue

            frame_age = current_time - latest_frame_time if latest_frame_time else float('inf')
            if frame_age > 1.0:
                # 检查帧是否太旧（超过1秒的帧丢弃）
                continue

            # 开始处理这一帧
            processing_start_time = current_time
            last_processing_time = current_time

            frame_timing = {
                'frame_id': self.frame_id,
                'frame_age': int(frame_age * 1000),  # 帧的年龄（毫秒）
            }

            # 1. 更新帧缓冲区
            with self.frame_lock:
                self.last_frame = frame
                self.display_frame = frame
                self.last_frame_time = latest_frame_time
                self.frame_buffer.append(frame)
                if len(self.frame_buffer) > self.max_buffer_size:
                    self.frame_buffer.pop(0)

            # 2. 进行YOLO检测和活动检测
            person_detected_raw = None
            if self.enable_yolo_processing:
                try:
                    yolo_start = time.time()
                    person_detected_raw = self._analyze_frame(
                        frame, frame_timing)
                    frame_timing['yolo'] = int(
                        (time.time() - yolo_start) * 1000)
                except Exception as e:
                    print(f"[VideoProcessor] YOLO分析出错: {e}")
                    frame_timing['yolo'] = -1
            else:
                # 只做活动检测
                activity_start = time.time()
                self._detect_activity()
                frame_timing['activity'] = int(
                    (time.time() - activity_start) * 1000)
                frame_timing['yolo'] = 0

            # 3. 记录处理时间和状态
            processing_end_time = time.time()
            frame_timing['total'] = int(
                (processing_end_time - processing_start_time) * 1000)
            frame_timing['person_detected'] = self.person_detected
            frame_timing['person_detected_raw'] = person_detected_raw
            frame_timing['is_active'] = self.is_active
            frame_timing['cup_detected'] = self.cup_detected

            self._write_timing_log(frame_timing, detailed=True)

            self.frame_id += 1

    
    def _analyze_frame(self, frame, frame_timing=None):
        """
        分析视频帧（合并YOLO检测）
        参数:
            frame: 要分析的视频帧
            frame_timing: 用于记录各阶段耗时的字典
        返回:
            person_detected_raw: YOLO本次检测到人的布尔值
        """
        # 1. 合并YOLO检测
        yolo_start = time.time()
        person_detected = False
        cup_detected = False
        if self.model is not None:
            try:
                results = self.model(frame)
                for result in results:
                    for box in result.boxes:
                        cls = int(box.cls[0])
                        if cls == 0:
                            person_detected = True
                        if cls == 41:
                            cup_detected = True
                # 只要检测到一次即可
            except Exception as e:
                print(f"YOLO检测出错: {e}")
        yolo_end = time.time()
        if frame_timing is not None:
            frame_timing['yolo'] = int((yolo_end - yolo_start) * 1000)
        # 2. 更新人体检测状态
        if person_detected:
            self.person_detected = True
            self.last_person_detection_time = time.time()
            self.person_absence_start_time = None
        else:
            if self.person_detected and not self.person_absence_start_time:
                self.person_absence_start_time = time.time()
            if self.person_absence_start_time:
                try:
                    absence_duration = (time.time() - self.person_absence_start_time)
                    if absence_duration > 2: # 2秒后认为人离开
                        self.person_detected = False
                except Exception as e:
                    import traceback
                    print("[DEBUG] absence_duration error:", e)
                    traceback.print_exc()
        # 3. 更新水杯检测状态
        if cup_detected:
            self.cup_detected = True
            self.last_cup_detection_time = time.time()
        else:
            if self.last_cup_detection_time:
                try:
                    no_cup_duration = (time.time() - self.last_cup_detection_time)
                    if no_cup_duration.total_seconds() > 5:
                        self.cup_detected = False
                except Exception as e:
                    import traceback
                    print("[DEBUG] no_cup_duration error:", e)
                    traceback.print_exc()
        # 4. 活动检测（帧差法）
        self._detect_activity()
        return person_detected
    
    def _detect_person(self, frame, return_raw=False):
        """
        兼容旧接口，直接返回 self.person_detected
        """
        if return_raw:
            return self.person_detected
    
    def _detect_cup(self, frame):
        """
        兼容旧接口，直接返回 self.cup_detected
        """
        return self.cup_detected
    
    def _detect_activity(self):
        """检测工人是否有活动"""
        if len(self.frame_buffer) < 2:
            return
        prev_frame = cv2.cvtColor(self.frame_buffer[-2], cv2.COLOR_BGR2GRAY)
        curr_frame = cv2.cvtColor(self.frame_buffer[-1], cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(prev_frame, curr_frame)
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        diff_ratio = np.sum(thresh) / (thresh.shape[0] * thresh.shape[1] * 255) * 100
        # 日志记录
        self._write_activity_log(self.frame_id, diff_ratio, self.is_active)
        if diff_ratio > self.activity_threshold:
            self.is_active = True
            self.last_activity_time = time.time()
        else:
            if self.last_activity_time:
                inactivity_duration = (time.time() - self.last_activity_time)
                try:
                    if inactivity_duration > 10:
                        self.is_active = False
                except Exception as e:
                    import traceback
                    print("[DEBUG] inactivity_duration error:", inactivity_duration)
                    traceback.print_exc()

    def _write_activity_log(self, frame_id, diff_ratio, is_active):
        """
        写入活动检测日志（每帧一条，便于分析阈值）
        """
        log_line = (
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] "
            f"frame_id={frame_id} diff_ratio={diff_ratio:.2f} is_active={is_active}\n"
        )
        with self.log_lock:
            with open(self.activity_log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line)

    def get_status(self):
        """获取当前状态"""
        return {
            "person_detected": self.person_detected,
            "is_active": self.is_active,
            "cup_detected": self.cup_detected,
            "last_frame_time": self.last_frame_time,
            "last_person_detection_time": self.last_person_detection_time,
            "last_activity_time": self.last_activity_time,
            "last_cup_detection_time": self.last_cup_detection_time
        }
    

    def get_latest_frame(self):
        """获取最新的视频帧（用于前端显示）"""
        frame, _ = self.camera.get_latest_frame()
        return frame
    
    def get_latest_frame_for_processing(self):
        """获取最新的视频帧（用于YOLO分析）"""
        with self.frame_lock:
            return self.last_frame
    
    def set_yolo_processing(self, enable):
        """设置是否启用YOLO处理"""
        self.enable_yolo_processing = enable
        return {"status": "success", "yolo_processing": enable}
    
    def _write_timing_log(self, timing, detailed=False):
        """
        写入检测耗时日志（线程安全）
        参数:
            timing: dict, 包含frame_id, fetch, yolo, cup, total等
            detailed: 是否写入详细状态信息
        """
        if not detailed:
            log_line = (
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] "
                f"frame_id={timing.get('frame_id', -1)} "
                f"fetch={timing.get('fetch', -1)}ms "
                f"yolo={timing.get('yolo', -1)}ms "
                f"cup={timing.get('cup', -1)}ms "
                f"total={timing.get('total', -1)}ms\n"
            )
        else:
            log_line = (
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] "
                f"frame_id={timing.get('frame_id', -1)} "
                f"fetch={timing.get('fetch', -1)}ms "
                f"yolo={timing.get('yolo', -1)}ms "
                f"cup={timing.get('cup', -1)}ms "
                f"total={timing.get('total', -1)}ms "
                f"person_detected={timing.get('person_detected', None)} "
                f"person_detected_raw={timing.get('person_detected_raw', None)} "
                f"person_absence_start_time={timing.get('person_absence_start_time', None)} "
                f"last_person_detection_time={timing.get('last_person_detection_time', None)}\n"
            )
        with self.log_lock:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_line) 