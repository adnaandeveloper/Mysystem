from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import ActionLog

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    logs = s.query(ActionLog).filter_by(user_id=update.effective_user.id).order_by(ActionLog.timestamp.desc()).limit(50).all()
    s.close()
    text = "🕒 HISTORY\n\n" + "\n".join([f"{l.timestamp.strftime('%m-%d %H:%M')} - {l.action}: {l.details}" for l in logs]) if logs else "No history"
    await update.message.reply_text(text)
