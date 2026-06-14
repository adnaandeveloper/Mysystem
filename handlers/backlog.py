from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, User
from datetime import datetime

async def backlog_handler(update, context):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).limit(10).all()
    text = "\n".join([i.text for i in items]) or "Empty"
    kb = [[InlineKeyboardButton("Add", callback_data="backlog_add")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
    s.close()

async def backlog_callback(update, context):
    q = update.callback_query
    await q.answer()
    if q.data == "backlog_add":
        context.user_data["await_backlog"] = True
        await q.message.reply_text("Send text")

async def backlog_text(update, context):
    if not context.user_data.get("await_backlog"):
        return
    s = SessionLocal()
    s.add(BacklogItem(user_id=update.effective_user.id, text=update.message.text, created_at=datetime.utcnow()))
    s.commit()
    s.close()
    context.user_data["await_backlog"] = False
    await update.message.reply_text("Added")
