from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Date, ForeignKey, Text
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_allowed = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Copenhagen")
    prompt_hour = Column(Integer, default=7)
    prompt_minute = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)

class BacklogItem(Base):
    __tablename__ = 'backlog_items'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    text = Column(Text)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyTask(Base):
    __tablename__ = 'daily_tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    backlog_id = Column(Integer, nullable=True)
    text = Column(Text)
    date = Column(Date, index=True)
    status = Column(String(20), default="todo")
    created_at = Column(DateTime, default=datetime.utcnow)

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    name = Column(String(200))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HabitLog(Base):
    __tablename__ = 'habit_logs'
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    date = Column(Date, index=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
