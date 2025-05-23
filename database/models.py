from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 创建数据库连接
DATABASE_URL = "sqlite:///./health_monitoring.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class WorkingSession(Base):
    """工作会话记录表，记录每次工作的开始和结束时间"""
    __tablename__ = "working_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # 单位：分钟
    
class ActivityRecord(Base):
    """活动记录表，记录工人的活动状态"""
    __tablename__ = "activity_records"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=False)  # 是否有活动
    inactive_duration = Column(Float, nullable=True)  # 不活动持续时间（分钟）
    
class WaterIntake(Base):
    """喝水记录表，记录检测到水杯的时间"""
    __tablename__ = "water_intake"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    detected = Column(Boolean, default=False)  # 是否检测到水杯
    
class HealthMetrics(Base):
    """健康指标汇总表，记录每小时的健康状态评分"""
    __tablename__ = "health_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    
class SigninRecord(Base):
    """刷脸签到记录表"""
    __tablename__ = "signin_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # 识别到的姓名
    timestamp = Column(DateTime, default=datetime.now)
    image_path = Column(String, nullable=False)  # 签到图片保存路径
    result = Column(String, nullable=False)  # 签到结果描述
    
# 创建数据库表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 