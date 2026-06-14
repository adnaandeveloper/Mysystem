from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem
from datetime import datetime

async def backlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["await_backlog"] = True
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).order_by(BacklogItem.id.desc()).limit(5).all()
    s.close()
    preview = "\n".join([f"• {i.text}" for i in items]) or "empty"
    await update.message.reply_text(
        f"📥 BACKLOG MODE ON\n\nLast 5:\n{preview}\n\nSend each idea as a message.\nType 'done' to stop."
    )

async def backlog_callback(update, context):
    await update.callback_query.answer()

async def backlog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_backlog"):
        return
    
    text = update.message.text.strip()
    if text.lower() in ["done", "stop", "exit", "x"]:
        context.user_data["await_backlog"] = False
        await update.message.reply_text("✓ Backlog mode OFF")
        return

    s = SessionLocal()
    s.add(BacklogItem(user_id=update.effective_user.id, text=text, created_at=datetime.utcnow()))
    s.commit()
    s.close()
    await update.message.reply_text(f"✓ Added")