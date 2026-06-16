from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, ActionLog
from datetime import datetime

def log_action(user_id, action, details):
    s = SessionLocal()
    s.add(ActionLog(user_id=user_id, action=action, details=details))
    s.commit()
    s.close()

async def backlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["await_backlog"] = True
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).order_by(BacklogItem.id.desc()).all()
    s.close()

    kb = [[InlineKeyboardButton(f"❌ {i.text[:40]}", callback_data=f"bl_del_{i.id}")] for i in items]
    text = "📥 BACKLOG\n\nTap ❌ to delete. Type below to add:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def backlog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("bl_del_"):
        bid = int(q.data.split("_")[2])
        s = SessionLocal()
        item = s.query(BacklogItem).get(bid)
        if item and item.user_id == q.from_user.id:
            log_action(q.from_user.id, "delete_backlog", item.text)
            s.delete(item)
            s.commit()
        s.close()
    await backlog_handler(q, context)

async def backlog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_backlog"):
        return
    text = update.message.text.strip()
    if text.lower() in ["done","stop"]:
        context.user_data["await_backlog"] = False
        return
    s = SessionLocal()
    s.add(BacklogItem(user_id=update.effective_user.id, text=text))
    s.commit()
    s.close()
    log_action(update.effective_user.id, "add_backlog", text)
    await update.message.reply_text("✓")
    await backlog_handler(update, context)
