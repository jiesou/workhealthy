import time
import threading
from datetime import datetime, timedelta # Ensure timedelta is here
# from turtle import st # Removed unused import
# from sqlalchemy.orm import Session # Session not directly used in this file
from database import crud, get_db
from .video_processor import VideoProcessor
from .genterator import GeneratorService
from .health_analyze import HealthAnalyze
import os


class Monitor:
    """监测服务，整合视频处理和健康分析处理操作"""

    def __init__(self, video_url=None):
        """
        初始化健康监测服务

        参数:
            video_url: 视频流URL，如果为None则使用环境变量或默认值
        """
        # 如果没有提供视频URL，则使用环境变量或默认值
        if video_url is None:
            # 尝试从环境变量获取，如果没有则使用默认值
            video_url = os.getenv("VIDEO_URL", "0")  # 默认使用本地摄像头

        self.video_processor = VideoProcessor(video_url)
        self.generator_service = GeneratorService()
        self.health_analyze = HealthAnalyze(self.video_processor) # Changed instantiation
        self.is_running = False
        self.monitor_thread = None
        self.video_url = video_url # Store video_url for use in output_insights

    def start(self):
        """启动健康监测服务"""
        if not self.is_running:
            self.is_running = True
            # 启动健康分析服务
            self.health_analyze.start()

            print("健康监测服务已启动")

    def stop(self):
        """停止健康监测服务"""
        self.is_running = False
        # 停止健康分析服务
        self.health_analyze.stop()

        print("健康监测服务已停止")

    def output_insights(self):
        """获取当前状态见解 胖服务端策略：字符串在服务端合成"""
        insights = {}
        db = None  # Initialize db to None for the finally block

        # Get today's work duration from database
        try:
            db = next(get_db())
            # Use self.video_url which was stored during __init__
            today_work_duration_seconds = crud.get_today_work_duration(db, self.video_url)

            # Format the message
            # Ensure today_work_duration_seconds is treated as int for timedelta
            formatted_duration = str(timedelta(seconds=int(today_work_duration_seconds or 0)))
            insights["today_work_duration_message"] = f"今日在岗: {formatted_duration}"
            if today_work_duration_seconds and today_work_duration_seconds >= 120: # Original threshold was 120 seconds
                insights["today_work_duration_message"] += "\n已工作较长时间, 注意休息!"
            elif today_work_duration_seconds and today_work_duration_seconds > 0:
                insights["today_work_duration_message"] += "\n请继续保持！"
            else:
                insights["today_work_duration_message"] += "\n暂无工作记录"

        except Exception as e:
            print(f"在数据库获取今日工作时长时出错: {e}")
            insights["today_work_duration_message"] = "获取工作时长信息时出错。"
        finally:
            if db: # Check if db was successfully assigned
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

        return insights

    def refresh_generator_summary_health(self):
        """刷新生成器摘要"""
        self.generator_service.refresh_summary_health(
            self.video_processor.status)
