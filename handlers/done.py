from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DoneItem, User

async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        items = session.query(DoneItem).filter_by(user_id=user.id).order_by(DoneItem.completed_at.desc()).limit(20).all()
        if not items:
            await update.message.reply_text("📦 No completed tasks yet.")
            return
        text = "📦 Completed:
" + "
".join([f"• {i.text}" for i in items])
        await update.message.reply_text(text)
    finally:
        session.close()
