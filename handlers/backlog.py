from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, User
from datetime import datetime

async def backlog_handler(update, context):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if not user or not user.is_allowed:
        session.close(); return
    items = session.query(BacklogItem).filter_by(user_id=user.telegram_id, archived=False).order_by(BacklogItem.created_at.desc()).limit(15).all()
    text = "📥 *Backlog*:

" + "
".join([f"{i+1}. {it.text}" for i,it in enumerate(items)]) if items else "Empty"
    kb = [[InlineKeyboardButton("➕ Add", callback_data="backlog_add")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    session.close()

async def backlog_callback(update, context):
    q = update.callback_query; await q.answer()
    if q.data == "backlog_add":
        context.user_data["awaiting_backlog"] = True
        await q.message.reply_text("Send idea:")

async def backlog_text(update, context):
    if not context.user_data.get("awaiting_backlog"): return
    session = SessionLocal()
    session.add(BacklogItem(user_id=update.effective_user.id, text=update.message.text, created_at=datetime.utcnow()))
    session.commit(); session.close()
    context.user_data["awaiting_backlog"] = False
    await update.message.reply_text("✅ Added")
