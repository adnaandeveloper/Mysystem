from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_allowed = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Copenhagen")
    created_at = Column(DateTime, default=datetime.utcnow)

class BacklogItem(Base):
    __tablename__ = "backlog"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    text = Column(Text)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    backlog_id = Column(Integer, nullable=True)
    text = Column(Text)
    date = Column(Date, index=True)
    status = Column(String(20), default="todo")  # todo, done
    created_at = Column(DateTime, default=datetime.utcnow)

class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    name = Column(String(200))
    active = Column(Boolean, default=True)
    recurrence_type = Column(String(20), default="daily")  # daily, weekly, custom, yearly
    recurrence_days = Column(String(20), nullable=True)  # e.g. "0,3" for Mon,Thu
    recurrence_month = Column(Integer, nullable=True)
    recurrence_day = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HabitLog(Base):
    __tablename__ = "habit_logs"
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, index=True)
    date = Column(Date, index=True)
    completed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionLog(Base):
    __tablename__ = "action_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    action = Column(String(50))  # add_backlog, delete_backlog, pick_today, complete_task, add_habit, etc
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
