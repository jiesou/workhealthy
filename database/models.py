import time
from sqlalchemy import Column, Integer, String, Boolean, create_engine
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
    start_time = Column(Integer)  # Store as Unix timestamp
    end_time = Column(Integer, nullable=True)  # Store as Unix timestamp
    monitor_video_url = Column(String, nullable=False)
    duration_seconds = Column(Integer, nullable=True)

class SigninRecord(Base):
    """刷脸签到记录表"""
    __tablename__ = "signin_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Integer, default=int(time.time()))
    name = Column(String, nullable=False)  # 识别到的姓名
    has_work_label = Column(Boolean, default=False)  # 是否有带工牌
    image_path = Column(String, nullable=False)  # 签到图片，格式为 "signin_{timestamp}.jpg"，使用时需要拼接 SIGNIN_IMAGES_PATH
    
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