from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, TodayItem, User, HistoryLog

async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.data.startswith("pick_"):
        return
    
    item_id = int(query.data.split("_")[1])
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        backlog = session.query(BacklogItem).filter_by(id=item_id, user_id=user.id).first()
        if backlog:
            # Check if already in today
            exists = session.query(TodayItem).filter_by(user_id=user.id, backlog_id=backlog.id, done=False).first()
            if not exists:
                today = TodayItem(user_id=user.id, backlog_id=backlog.id, text=backlog.text)
                session.add(today)
                session.add(HistoryLog(user_id=user.id, action="plan_add", detail=backlog.text))
                session.commit()
                await query.message.reply_text(f"➕ Added to Today: {backlog.text}")
            else:
                await query.message.reply_text("Already in Today")
    finally:
        session.close()
