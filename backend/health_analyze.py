import time
import threading
from datetime import datetime, timedelta
from charset_normalizer import detect
from sqlalchemy.orm import Session
from backend.video_processor import VideoProcessor
from database import crud, get_db
import traceback


class HealthAnalyze:
    """健康分析服务，处理基于时间间隔的健康数据分析"""

    ACTIVITY_CHECK_INTERVAL = 60  # 每分钟检查一次活动状态
    WATER_CHECK_INTERVAL = 300  # 每5分钟检查一次喝水状态
    HEALTH_METRICS_INTERVAL = 3600  # 每小时计算一次健康指标

    def __init__(self, video_processor: VideoProcessor):
        """初始化健康分析服务"""
        self.video_processor = video_processor
        self.detection_status = self.video_processor.status

        self.is_running = False
        self.analyze_thread = None

        # 上次检查时间
        self.last_activity_check = None
        self.last_water_check = None
        self.last_health_metrics = None

        # 不活动计时器
        self.inactive_start_time = None

        # 当前工作会话ID
        self.current_working_session_id = None

    def start(self):
        """启动健康分析服务"""
        if not self.is_running:
            self.is_running = True
            # 启动分析线程
            self.analyze_thread = threading.Thread(target=self._analyze_loop)
            self.analyze_thread.daemon = True
            self.analyze_thread.start()

            print("健康分析服务已启动")

    def stop(self):
        """停止健康分析服务"""
        self.is_running = False
        # 等待分析线程结束
        if self.analyze_thread:
            self.analyze_thread.join()

        # 结束当前工作会话
        if self.current_working_session_id:
            db = next(get_db())
            try:
                crud.end_working_session(db, self.current_working_session_id)
                self.current_working_session_id = None
            finally:
                db.close()

        print("健康分析服务已停止")

    def _analyze_loop(self):
        """分析主循环"""
        while self.is_running:
            try:
                # 获取数据库会话
                db = next(get_db())

                current_time = datetime.now()

                # 更新工作状态
                self.process_working_session(
                    self.detection_status.is_person_detected)

                # 1. 检查活动状态
                if (not self.last_activity_check or
                        (current_time - self.last_activity_check).total_seconds() >= self.ACTIVITY_CHECK_INTERVAL):
                    self.process_activity_status(db)
                    self.last_activity_check = current_time

                # 2. 检查喝水状态
                if (not self.last_water_check or
                        (current_time - self.last_water_check).total_seconds() >= self.WATER_CHECK_INTERVAL):
                    self.process_water_intake(db)
                    self.last_water_check = current_time

                # 3. 计算健康指标
                if (not self.last_health_metrics or
                        (current_time - self.last_health_metrics).total_seconds() >= self.HEALTH_METRICS_INTERVAL):
                    crud.calculate_health_metrics(db)
                    self.last_health_metrics = current_time

            except Exception as e:
                print(f"分析过程中出错: {e}")
                traceback.print_exc()
            finally:
                # 确保数据库连接被正确关闭
                if 'db' in locals():
                    try:
                        db.close()
                    except Exception as e:
                        print(f"关闭数据库连接时出错: {e}")

            # 每秒检查一次
            time.sleep(1)

    def process_working_session(self, is_person_detected):
        """
        处理工作会话状态

        参数:
            is_person_detected: 是否检测到人
        """
        db = next(get_db())
        try:
            # 如果检测到人，但没有活动的工作会话，则创建新会话
            if is_person_detected and not self.current_working_session_id:
                session = crud.start_working_session(db)
                self.current_working_session_id = session.id
            # 如果没有检测到人，但有活动的工作会话，则结束会话
            elif not is_person_detected and self.current_working_session_id:
                crud.end_working_session(db, self.current_working_session_id)
                self.current_working_session_id = None
        finally:
            db.close()

    def process_activity_status(self, db: Session):
        """
        处理活动状态

        参数:
            db: 数据库会话
        """
        # 如果有人在工位
        if self.detection_status.is_person_detected:
            # 记录活动状态
            if self.detection_status.is_active:
                # 如果之前不活动，计算不活动持续时间
                inactive_duration = None
                if self.inactive_start_time:
                    inactive_duration = (
                        datetime.now() - self.inactive_start_time).total_seconds() / 60
                    self.inactive_start_time = None

                crud.record_activity(db, True, inactive_duration)
            else:
                # 如果开始不活动，记录开始时间
                if not self.inactive_start_time:
                    self.inactive_start_time = datetime.now()

                crud.record_activity(db, False, None)

    def process_water_intake(self, db: Session):
        """
        处理喝水状态

        参数:
            db: 数据库会话
            cup_detected: 是否检测到水杯
        """
        # 记录是否检测到水杯
        if self.detection_status.is_cup_detected:
            crud.record_water_intake(db, self.detection_status.is_cup_detected)
