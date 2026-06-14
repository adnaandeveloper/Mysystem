from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit
from datetime import datetime

async def habit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["await_habit"] = True
    s = SessionLocal()
    hs = s.query(Habit).filter_by(user_id=update.effective_user.id, active=True).all()
    s.close()
    preview = "\n".join([f"• {h.name}" for h in hs]) or "none yet"
    await update.message.reply_text(
        f"🔥 HABIT MODE ON\n\nCurrent:\n{preview}\n\nSend each habit name.\nType 'done' to stop."
    )

async def habit_callback(update, context):
    await update.callback_query.answer()

async def habit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("await_habit"):
        return
    
    text = update.message.text.strip()
    if text.lower() in ["done", "stop", "exit", "x"]:
        context.user_data["await_habit"] = False
        await update.message.reply_text("✓ Habit mode OFF")
        return

    s = SessionLocal()
    s.add(Habit(user_id=update.effective_user.id, name=text, created_at=datetime.utcnow()))
    s.commit()
    s.close()
    await update.message.reply_text(f"✓ Habit added")