from telegram import Update
from telegram.ext import ContextTypes
from handlers.backlog import backlog_handler, backlog_text
from handlers.today import today_handler
from handlers.habits import habits_handler, habits_text
from handlers.done import done_handler
from handlers.history import history_handler
from handlers.admin import admin_handler, admin_text
from db import SessionLocal
from models import User
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = SessionLocal()
    try:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user or (not db_user.is_allowed and user.id != ADMIN_ID):
            await update.message.reply_text("🚫 Not allowed.")
            return
        
        text = update.message.text
        state = context.user_data.get("awaiting")
        
        # State-based routing first
        if state:
            if state == "backlog_add":
                return await backlog_text(update, context)
            if state in ["habit_name", "habit_recurrence"]:
                return await habits_text(update, context)
            if state.startswith("admin_"):
                return await admin_text(update, context)
        
        # Menu routing
        if text == "📥 Backlog":
            return await backlog_handler(update, context)
        elif text == "✅ Today":
            return await today_handler(update, context)
        elif text == "🔥 Habits":
            return await habits_handler(update, context)
        elif text == "📦 All Tasks":
            return await done_handler(update, context)
        elif text == "📜 History":
            return await history_handler(update, context)
        elif text == "⚙️ Admin":
            return await admin_handler(update, context)
    finally:
        session.close()
