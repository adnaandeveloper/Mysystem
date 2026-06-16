from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import HistoryLog, User

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        logs = session.query(HistoryLog).filter_by(user_id=user.id).order_by(HistoryLog.created_at.desc()).limit(15).all()
        if not logs:
            await update.message.reply_text("📜 No history yet.")
            return
        text = "📜 History:
" + "
".join([f"{l.created_at.strftime('%m-%d %H:%M')} - {l.action}: {l.detail}" for l in logs])
        await update.message.reply_text(text)
    finally:
        session.close()
