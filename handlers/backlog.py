from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, User, HistoryLog

async def backlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting"] = "backlog_add"
    await update.message.reply_text("📥 Send me a task to add to Backlog (or /cancel):")

async def backlog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting") != "backlog_add":
        return
    text = update.message.text
    if text == "/cancel":
        context.user_data["awaiting"] = None
        await update.message.reply_text("Cancelled.")
        return
    
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        item = BacklogItem(user_id=user.id, text=text)
        session.add(item)
        session.add(HistoryLog(user_id=user.id, action="backlog_add", detail=text))
        session.commit()
        context.user_data["awaiting"] = None
        await update.message.reply_text(f"✅ Added to Backlog: {text}")
    finally:
        session.close()

async def backlog_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        items = session.query(BacklogItem).filter_by(user_id=user.id).order_by(BacklogItem.created_at.desc()).all()
        if not items:
            await update.callback_query.message.reply_text("Backlog is empty.")
            return
        keyboard = [[InlineKeyboardButton(f"➕ {i.text[:30]}", callback_data=f"bl_add_{i.id}")] for i in items]
        await update.callback_query.message.reply_text("Pick tasks to add to Today:", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        session.close()
