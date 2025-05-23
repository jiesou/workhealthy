from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from . import models

def start_working_session(db: Session):
    """开始一个新的工作会话"""
    session = models.WorkingSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def end_working_session(db: Session, session_id: int):
    """结束一个工作会话"""
    session = db.query(models.WorkingSession).filter(models.WorkingSession.id == session_id).first()
    if session and not session.end_time:
        session.end_time = datetime.now()
        # 计算持续时间（分钟）
        duration = (session.end_time - session.start_time).total_seconds() / 60
        session.duration = duration
        db.commit()
        db.refresh(session)
    return session

def record_activity(db: Session, is_active: bool, inactive_duration: float = None):
    """记录活动状态"""
    activity = models.ActivityRecord(is_active=is_active, inactive_duration=inactive_duration)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

def record_water_intake(db: Session, detected: bool):
    """记录喝水情况"""
    water_record = models.WaterIntake(detected=detected)
    db.add(water_record)
    db.commit()
    db.refresh(water_record)
    return water_record

def calculate_health_metrics(db: Session):
    """计算健康指标"""
    # 获取最近一小时的数据
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    # 计算工作时长评分
    working_sessions = db.query(models.WorkingSession).filter(
        models.WorkingSession.start_time >= one_hour_ago
    ).all()
    total_work_minutes = sum([
        ((s.end_time or datetime.now()) - s.start_time).total_seconds() / 60
        for s in working_sessions
    ])
    # 如果工作时间超过50分钟/小时，分数开始降低
    # work_duration_score = max(0, 100 - max(0, total_work_minutes - 50) * 2)
    
    # 计算活动频率评分
    activity_records = db.query(models.ActivityRecord).filter(
        models.ActivityRecord.timestamp >= one_hour_ago
    ).all()
    inactive_periods = [r.inactive_duration for r in activity_records if r.inactive_duration]
    if inactive_periods:
        max_inactive_time = max(inactive_periods)
        # 如果最长不活动时间超过20分钟，分数开始降低
        # activity_score = max(0, 100 - max(0, max_inactive_time - 20) * 5)
    else:
        # activity_score = 100
        pass
    
    # 计算喝水频率评分
    water_records = db.query(models.WaterIntake).filter(
        models.WaterIntake.timestamp >= one_hour_ago,
        models.WaterIntake.detected == True
    ).count()
    # 每小时至少喝一次水，得满分
    # water_intake_score = min(100, water_records * 100)
    
    # 计算综合健康评分
    # overall_health_score = np.mean([work_duration_score, activity_score, water_intake_score])
    
    # 保存健康指标
    health_metrics = models.HealthMetrics(
        # work_duration_score=work_duration_score,
        # activity_score=activity_score,
        # water_intake_score=water_intake_score,
        # overall_health_score=overall_health_score
    )
    db.add(health_metrics)
    db.commit()
    db.refresh(health_metrics)
    return health_metrics

def get_latest_health_metrics(db: Session):
    """获取最新的健康指标"""
    return db.query(models.HealthMetrics).order_by(models.HealthMetrics.timestamp.desc()).first()

def get_health_metrics_history(db: Session, days: int = 7):
    """获取过去几天的健康指标历史"""
    start_date = datetime.now() - timedelta(days=days)
    return db.query(models.HealthMetrics).filter(
        models.HealthMetrics.timestamp >= start_date
    ).order_by(models.HealthMetrics.timestamp).all()

def get_today_work_duration(db: Session):
    """
    获取今天累计在岗时长（单位：秒）。
    包括已结束和正在进行的会话。
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    sessions = db.query(models.WorkingSession).filter(models.WorkingSession.start_time >= today_start).all()
    total_seconds = 0
    now = datetime.now()
    for s in sessions:
        if s.end_time:
            total_seconds += (s.end_time - s.start_time).total_seconds()
        else:
            total_seconds += (now - s.start_time).total_seconds()
    return int(total_seconds)

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