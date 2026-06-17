from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DoneItem, User
from datetime import datetime, timedelta
import pytz

async def done_today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        # Get today in Copenhagen time
        tz = pytz.timezone('Europe/Copenhagen')
        now = datetime.now(tz)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # Convert to UTC for DB query (assuming DB stores UTC)
        today_start_utc = today_start.astimezone(pytz.UTC)
        today_end_utc = today_end.astimezone(pytz.UTC)

        items = session.query(DoneItem).filter(
            DoneItem.user_id == user.id,
            DoneItem.completed_at >= today_start_utc,
            DoneItem.completed_at < today_end_utc
        ).order_by(DoneItem.completed_at.desc()).all()

        if not items:
            text = "📭 Nothing done today yet.\n\nGo crush your Today list!"
        else:
            text = f"✅ Done Today ({len(items)})\n\n"
            for i, item in enumerate(items, 1):
                time_str = item.completed_at.astimezone(tz).strftime("%H:%M")
                text += f"{i}. {item.text} — {time_str}\n"

        await update.message.reply_text(text)
    finally:
        session.close()