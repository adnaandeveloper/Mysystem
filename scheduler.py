from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import SessionLocal
from models import User
from datetime import datetime
import pytz

scheduler = AsyncIOScheduler(timezone="UTC")

async def send_prompts(app):
    session = SessionLocal()
    for u in session.query(User).filter_by(is_allowed=True).all():
        try:
            tz = pytz.timezone(u.timezone or "Europe/Copenhagen")
            now = datetime.now(tz)
            if now.hour == u.prompt_hour and now.minute < 5:
                await app.bot.send_message(u.telegram_id, "Morning! Use /plan")
        except Exception:
            pass
    session.close()

def setup_scheduler(app):
    scheduler.add_job(send_prompts, 'cron', minute='0-5', args=[app])
    scheduler.start()
