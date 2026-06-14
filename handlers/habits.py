from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, HabitLog
from datetime import date

async def habit_handler(update, context):
    s = SessionLocal()
    if context.args and context.args[0] == "add":
        name = " ".join(context.args[1:])
        s.add(Habit(user_id=update.effective_user.id, name=name))
        s.commit()
        await update.message.reply_text("Added")
    else:
        hs = s.query(Habit).filter_by(user_id=update.effective_user.id).all()
        await update.message.reply_text("\n".join([h.name for h in hs]) or "No habits")
    s.close()

async def habit_callback(update, context):
    await update.callback_query.answer()
