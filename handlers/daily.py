from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DailyTask, BacklogItem
from datetime import date

async def today_handler(update, context):
    s = SessionLocal()
    tasks = s.query(DailyTask).filter_by(user_id=update.effective_user.id, date=date.today()).all()
    txt = "\n".join([t.text for t in tasks]) or "No tasks"
    await update.message.reply_text(txt)
    s.close()

async def plan_handler(update, context):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).limit(10).all()
    kb = [[InlineKeyboardButton(i.text[:30], callback_data=f"pick_{i.id}")] for i in items]
    await update.message.reply_text("Pick", reply_markup=InlineKeyboardMarkup(kb))
    s.close()

async def daily_callback(update, context):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()
    if q.data.startswith("pick_"):
        bid = int(q.data.split("_")[1])
        it = s.query(BacklogItem).get(bid)
        s.add(DailyTask(user_id=q.from_user.id, backlog_id=bid, text=it.text, date=date.today()))
        s.commit()
    s.close()

async def daily_text(update, context):
    pass
