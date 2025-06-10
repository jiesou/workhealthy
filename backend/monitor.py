import time
import threading
from datetime import datetime, timedelta
from turtle import st
from sqlalchemy.orm import Session
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
        self.health_analyze = HealthAnalyze(self.video_processor)
        self.is_running = False
        self.monitor_thread = None

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

        # 需要在数据库中获取的健康指标
        try:
            db = next(get_db())
            # 获取最新的健康指标
            health_metrics = crud.get_latest_health_metrics(db)
            # 获取今日累计在岗时长（秒）
            today_work_duration = crud.get_today_work_duration(db)

            # 今日在岗时长消息
            insights["today_work_duration_message"] = "今日在岗: "
            insights["today_work_duration_message"] += str(
                timedelta(seconds=today_work_duration))
            if today_work_duration >= 120:
                insights["today_work_duration_message"] += "，已工作较长时间"
            else:
                insights["today_work_duration_message"] += "，请继续保持！"

        except Exception as e:
            print(f"在数据库获取健康指标时出错: {e}")
        finally:
            if 'db' in locals():
                try:
                    db.close()
                except Exception as e:
                    print(f"关闭数据库连接时出错: {e}")

        # 添加 AI 摘要健康信息
        insights["generator_summary_health_message"] = self.generator_service.summary_health_message

        # 添加喝水状态消息
        if self.video_processor.status.is_cup_detected:
            insights["water_intake_message"] = "检测到水杯，请及时喝水！"
        else:
            insights["water_intake_message"] = "未检测到水杯，请注意补水！"

        return insights

    def refresh_generator_summary_health(self):
        """刷新生成器摘要"""
        self.generator_service.refresh_summary_health(
            self.video_processor.status)
