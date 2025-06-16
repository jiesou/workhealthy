import time
import threading
from datetime import datetime # timedelta removed
# from charset_normalizer import detect # This import seems unused
# from sqlalchemy.orm import Session # Session type hint no longer needed
from backend.video_processor import VideoProcessor
from database import crud, get_db
import traceback


class HealthAnalyze:
    """健康分析服务，处理基于时间间隔的健康数据分析"""

    # ACTIVITY_CHECK_INTERVAL, WATER_CHECK_INTERVAL, HEALTH_METRICS_INTERVAL removed

    def __init__(self, video_processor: VideoProcessor): # monitor_video_url parameter removed
        """初始化健康分析服务"""
        self.video_processor = video_processor
        self.detection_status = self.video_processor.status
        self.monitor_video_url = self.video_processor.video_url # Set from video_processor

        self.is_running = False
        self.analyze_thread = None

        # last_activity_check, last_water_check, last_health_metrics removed
        # inactive_start_time removed

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

                # current_time = datetime.now() # Removed as no longer directly used for interval checks

                # 更新工作状态
                self.process_working_session(
                    self.detection_status.is_person_detected)

                # Interval checks for activity, water, and health metrics removed

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
                session = crud.start_working_session(db, monitor_video_url=self.monitor_video_url) # Pass monitor_video_url
                self.current_working_session_id = session.id
            # 如果没有检测到人，但有活动的工作会话，则结束会话
            elif not is_person_detected and self.current_working_session_id:
                crud.end_working_session(db, self.current_working_session_id)
                self.current_working_session_id = None
        finally:
            db.close()

    # process_activity_status method removed
    # process_water_intake method removed
