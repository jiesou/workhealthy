import time
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import crud, get_db
from .video_processor import VideoProcessor
from .genterator import GeneratorService
import os
import traceback

class HealthMonitor:
    """健康监测服务，整合视频处理和数据库操作"""
    
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
        self.is_running = False
        self.monitor_thread = None
        self.current_session_id = None
        
        # 监控间隔（秒）
        self.activity_check_interval = 60  # 每分钟检查一次活动状态
        self.water_check_interval = 300  # 每5分钟检查一次喝水状态
        self.health_metrics_interval = 3600  # 每小时计算一次健康指标
        
        # 上次检查时间
        self.last_activity_check = None
        self.last_water_check = None
        self.last_health_metrics = None
        
        # 不活动计时器
        self.inactive_start_time = None
    
    def start(self):
        """启动健康监测服务"""
        if not self.is_running:
            self.is_running = True
            # 启动视频处理
            self.video_processor.start()
            # 启动监测线程
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            print("健康监测服务已启动")
    
    def stop(self):
        """停止健康监测服务"""
        self.is_running = False
        # 停止视频处理
        self.video_processor.stop()
        # 等待监测线程结束
        if self.monitor_thread:
            self.monitor_thread.join()
        
        # 结束当前工作会话
        if self.current_session_id:
            db = next(get_db())
            crud.end_working_session(db, self.current_session_id)
            self.current_session_id = None
        
        print("健康监测服务已停止")
    
    def _monitor_loop(self):
        """监测主循环"""
        while self.is_running:
            try:
                # 获取当前状态
                status = self.video_processor.get_status()
                
                # 获取数据库会话
                db = next(get_db())
                
                # 1. 检查工作状态
                self._check_working_status(db, status)
                
                # 2. 检查活动状态
                current_time = datetime.now()
                if (not self.last_activity_check or 
                    (current_time - self.last_activity_check).total_seconds() >= self.activity_check_interval):
                    self._check_activity_status(db, status)
                    self.last_activity_check = current_time
                
                # 3. 检查喝水状态
                if (not self.last_water_check or 
                    (current_time - self.last_water_check).total_seconds() >= self.water_check_interval):
                    self._check_water_intake(db, status)
                    self.last_water_check = current_time
                
                # 4. 计算健康指标
                if (not self.last_health_metrics or 
                    (current_time - self.last_health_metrics).total_seconds() >= self.health_metrics_interval):
                    crud.calculate_health_metrics(db)
                    self.last_health_metrics = current_time
                
            except Exception as e:
                print(f"监测过程中出错: {e}")
                traceback.print_exc()
            finally:
                # 确保数据库连接被正确关闭
                if db:
                    try:
                        db.close()
                    except Exception as e:
                        print(f"关闭数据库连接时出错: {e}")

            
            # 每秒检查一次
            time.sleep(1)
    
    def _check_working_status(self, db: Session, status):
        """
        检查工作状态
        
        参数:
            db: 数据库会话
            status: 当前状态
        """
        person_detected = status["person_detected"]
        
        # 如果检测到人，但没有活动的工作会话，则创建新会话
        if person_detected and not self.current_session_id:
            session = crud.start_working_session(db)
            self.current_session_id = session.id
        
        # 如果没有检测到人，但有活动的工作会话，则结束会话
        elif not person_detected and self.current_session_id:
            crud.end_working_session(db, self.current_session_id)
            self.current_session_id = None
    
    def _check_activity_status(self, db: Session, status):
        """
        检查活动状态
        
        参数:
            db: 数据库会话
            status: 当前状态
        """
        is_active = status["is_active"]
        
        # 如果有人在工位
        if status["person_detected"]:
            # 记录活动状态
            if is_active:
                # 如果之前不活动，计算不活动持续时间
                inactive_duration = None
                if self.inactive_start_time:
                    inactive_duration = (datetime.now() - self.inactive_start_time).total_seconds() / 60
                    self.inactive_start_time = None
                
                crud.record_activity(db, True, inactive_duration)
            else:
                # 如果开始不活动，记录开始时间
                if not self.inactive_start_time:
                    self.inactive_start_time = datetime.now()
                
                crud.record_activity(db, False, None)
    
    def _check_water_intake(self, db: Session, status):
        """
        检查喝水状态
        
        参数:
            db: 数据库会话
            status: 当前状态
        """
        cup_detected = status["cup_detected"]
        
        # 记录是否检测到水杯
        if status["person_detected"]:
            crud.record_water_intake(db, cup_detected)
    
    def get_status(self):
        """获取当前状态"""
        status = self.video_processor.get_status()
        
        # 添加额外信息
        status["current_session_id"] = self.current_session_id
        
        # 获取最新的健康指标
        try:
            db = next(get_db())
            health_metrics = crud.get_latest_health_metrics(db)
            if health_metrics:
                status["health_metrics"] = {
                    "timestamp": health_metrics.timestamp
                }
            # 新增：获取今日累计在岗时长（秒）
            today_work_duration = crud.get_today_work_duration(db)
            status["today_work_duration"] = today_work_duration
            status["generator_summary_health_message"] = self.generator_service.summary_health_message
        except Exception as e:
            print(f"获取健康指标或在岗时长时出错: {e}")
        finally:
            if db:
                try:
                    db.close()
                except Exception as e:
                    print(f"关闭数据库连接时出错: {e}")

        self.generator_service.update_data(status)
        return status
    
    def set_yolo_processing(self, enable):
        """设置是否启用YOLO处理"""
        return self.video_processor.set_yolo_processing(enable) 
    
    def refresh_generator_summary_health(self):
        """刷新生成器摘要"""
        self.generator_service.refresh_summary_health()
