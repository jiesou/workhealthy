from sqlalchemy.orm import Session
from datetime import datetime # Removed timedelta, kept datetime
import time # Added time
# import numpy as np # numpy seems no longer used
from . import models

def start_working_session(db: Session, monitor_video_url: str):
    """开始一个新的工作会话"""
    session = models.WorkingSession(start_time=int(time.time()), monitor_video_url=monitor_video_url)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def end_working_session(db: Session, session_id: int):
    """结束一个工作会话"""
    session = db.query(models.WorkingSession).filter(models.WorkingSession.id == session_id).first()
    if session and session.end_time is None: # Check if end_time is None
        session.end_time = int(time.time())
        # 计算持续时间（秒）
        if session.start_time: # Ensure start_time is not None
            session.duration_seconds = session.end_time - session.start_time
        db.commit()
        db.refresh(session)
    return session

def get_today_work_duration(db: Session, monitor_video_url: str) -> int:
    """
    获取今天累计在岗时长（单位：秒）。
    包括已结束和正在进行的会话。
    """
    today_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_ts = int(today_start_dt.timestamp())

    sessions = db.query(models.WorkingSession).filter(
        models.WorkingSession.monitor_video_url == monitor_video_url,
        models.WorkingSession.start_time >= today_start_ts
    ).all()

    total_seconds = 0
    current_ts = int(time.time())
    for s in sessions:
        if s.end_time is not None and s.duration_seconds is not None:
            total_seconds += s.duration_seconds
        elif s.start_time is not None: # Session is ongoing or duration_seconds was not set for some reason
            # If end_time is None, it's an ongoing session
            # If end_time is not None but duration_seconds is None, calculate it now (should not happen with new logic)
            end_or_current_time = s.end_time if s.end_time is not None else current_ts
            total_seconds += (end_or_current_time - s.start_time)
    return total_seconds

def get_work_sessions_for_period(db: Session, monitor_video_url: str, start_date_ts: int, end_date_ts: int):
    """获取指定时间段内特定监控视频的工作会话记录"""
    return db.query(models.WorkingSession).filter(
        models.WorkingSession.monitor_video_url == monitor_video_url,
        models.WorkingSession.start_time >= start_date_ts,
        models.WorkingSession.start_time <= end_date_ts
    ).order_by(models.WorkingSession.start_time).all()

def create_signin_record(db: Session, name: str, image_path: str, result: str):
    """新增刷脸签到记录"""
    record = models.SigninRecord(name=name, image_path=image_path, result=result)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_signin_records(db: Session, limit: int = 100):
    """获取最近的刷脸签到记录"""
    return db.query(models.SigninRecord).order_by(models.SigninRecord.timestamp.desc()).limit(limit).all() 