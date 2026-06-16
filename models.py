from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    is_admin = Column(Boolean, default=False)
    is_allowed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class BacklogItem(Base):
    __tablename__ = "backlog"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class TodayItem(Base):
    __tablename__ = "today"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    backlog_id = Column(Integer, ForeignKey("backlog.id"), nullable=True)
    text = Column(Text, nullable=False)
    done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
class DoneItem(Base):
    __tablename__ = "done"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
class Habit(Base):
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    recurrence = Column(String, default="daily")
    streak = Column(Integer, default=0)
    last_done = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
class HistoryLog(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
