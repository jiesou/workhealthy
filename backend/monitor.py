import time
import threading
from datetime import datetime, timedelta  # Ensure timedelta is here
# from turtle import st # Removed unused import
# from sqlalchemy.orm import Session # Session not directly used in this file
from database import crud, get_db
from .video_processor import VideoProcessor
from .genterator import GeneratorService
from .health_analyze import HealthAnalyze
from .current import CurrentProcessor
import os


class Monitor:
    """监测服务，整合视频处理和健康分析处理操作"""

    def __init__(self, video_url: str, current_sensor_url: str):
        """
        初始化健康监测服务

        参数:
            video_url: 视频流URL
            current_sensor_url: 当前传感器的HTTP URL（可选）
        """

        self.video_processor = VideoProcessor(video_url)
        if current_sensor_url is not None:
            self.current_processor = CurrentProcessor(current_sensor_url)
        self.health_analyze = HealthAnalyze(self.video_processor)
        self.generator_service = GeneratorService()

        self.is_running = False
        self.monitor_thread = None

    def start(self):
        """启动健康监测服务"""
        if not self.is_running:
            self.is_running = True
            # 启动健康分析服务
            self.health_analyze.start()

            print("[Bootstrap] 健康监测服务已启动")

    def stop(self):
        """停止健康监测服务"""
        self.is_running = False
        # 停止健康分析服务
        self.health_analyze.stop()

        print("健康监测服务已停止")

    def output_insights(self):
        """获取当前状态见解 胖服务端策略：字符串在服务端合成"""
        insights = {}
        db = None

        # 需要数据库的
        try:
            db = next(get_db())
            today_work_duration_seconds = crud.get_today_work_duration(
                db, self.video_processor.video_url)

            # today_work_duration_seconds 是 timedelta 的 int
            formatted_duration = str(
                timedelta(seconds=int(today_work_duration_seconds or 0)))
            insights["today_work_duration_message"] = f"{formatted_duration}"
            if today_work_duration_seconds and today_work_duration_seconds >= 120:  # Original threshold was 120 seconds
                insights["today_work_duration_message"] += "\n已工作较长时间!"
            elif today_work_duration_seconds and today_work_duration_seconds > 0:
                insights["today_work_duration_message"] += "\n请继续保持！"
            else:
                insights["today_work_duration_message"] += "\n暂无工作记录"

        except Exception as e:
            print(f"在数据库获取今日工作时长时出错: {e}")
            insights["today_work_duration_message"] = "获取工作时长信息时出错。"
        finally:
            if db:  # Check if db was successfully assigned
                try:
                    db.close()
                except Exception as e:
                    print(f"关闭数据库连接时出错: {e}")

        # Add AI generator summary
        if hasattr(self, 'generator_service') and hasattr(self.generator_service, 'summary_health_message'):
            insights["generator_summary_health_message"] = self.generator_service.summary_health_message
        else:
            insights["generator_summary_health_message"] = "AI健康摘要服务不可用。"

        # Add water intake message
        if hasattr(self, 'video_processor') and hasattr(self.video_processor, 'status'):
            if self.video_processor.status.is_cup_detected:
                insights["water_intake_message"] = "检测到水杯，请及时喝水！"
            else:
                insights["water_intake_message"] = "未检测到水杯，请注意补水！"
        else:
            insights["water_intake_message"] = "水杯检测状态不可用。"

        if hasattr(self, 'current_processor'):
            insights["current_power_message"] = f"{self.current_processor.power:.2f} W"

        return insights

    def refresh_generator_summary_health(self):
        """刷新生成器摘要"""
        self.generator_service.refresh_summary_health(
            self.video_processor.status)
