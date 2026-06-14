from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import SessionLocal
from models import User
from datetime import datetime
import pytz

scheduler = AsyncIOScheduler(timezone="UTC")

async def send_morning_prompt(app):
    session = SessionLocal()
    users = session.query(User).filter(User.is_allowed==True).all()
    for u in users:
        try:
            tz = pytz.timezone(u.timezone or "Europe/Copenhagen")
            now = datetime.now(tz)
            if now.hour == u.prompt_hour and now.minute < 5:
                await app.bot.send_message(
                    chat_id=u.telegram_id,
                    text=f"🌅 Good morning ({tz.zone})! /plan to set tasks"
                )
        except Exception as e:
            print(f"Prompt failed: {e}")
    session.close()

async def send_evening_prompt(app):
    session = SessionLocal()
    users = session.query(User).filter(User.is_allowed==True).all()
    for u in users:
        try:
            tz = pytz.timezone(u.timezone or "Europe/Copenhagen")
            now = datetime.now(tz)
            if now.hour == 21:
                await app.bot.send_message(
                    chat_id=u.telegram_id,
                    text="🌙 Evening check-in: /today + /habit"
                )
        except:
            pass
    session.close()

def setup_scheduler(app):
    scheduler.add_job(send_morning_prompt, 'cron', minute='0-5', args=[app], id="morning")
    scheduler.add_job(send_evening_prompt, 'cron', minute=0, args=[app], id="evening")
    scheduler.start()
