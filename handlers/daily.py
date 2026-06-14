from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DailyTask, BacklogItem
from datetime import date, timedelta

async def today_handler(update, context):
    s = SessionLocal(); tasks = s.query(DailyTask).filter_by(user_id=update.effective_user.id, date=date.today()).all()
    if not tasks: await update.message.reply_text("No tasks. /plan"); s.close(); return
    txt = "🎯 Today:
"; kb=[]
    for t in tasks:
        txt += f"{'✅' if t.status=='done' else '⬜'} {t.text}
"
        kb.append([InlineKeyboardButton(t.text[:30], callback_data=f"toggle_{t.id}")])
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb)); s.close()

async def plan_handler(update, context):
    s = SessionLocal(); uid=update.effective_user.id
    y = date.today()-timedelta(days=1)
    for t in s.query(DailyTask).filter_by(user_id=uid, date=y, status="todo").all(): t.date=date.today()
    s.commit()
    items = s.query(BacklogItem).filter_by(user_id=uid, archived=False).limit(10).all()
    kb = [[InlineKeyboardButton(i.text[:35], callback_data=f"pick_{i.id}")] for i in items]
    kb.append([InlineKeyboardButton("✏️ New", callback_data="daily_new")])
    await update.message.reply_text("Pick for today:", reply_markup=InlineKeyboardMarkup(kb)); s.close()

async def daily_callback(update, context):
    q=update.callback_query; await q.answer(); s=SessionLocal()
    d=q.data
    if d.startswith("pick_"):
        b=int(d.split("_")[1]); it=s.query(BacklogItem).get(b)
        s.add(DailyTask(user_id=q.from_user.id, backlog_id=b, text=it.text, date=date.today())); s.commit()
        await q.message.reply_text(f"Added {it.text}")
    elif d.startswith("toggle_"):
        t=s.query(DailyTask).get(int(d.split("_")[1])); t.status="done" if t.status!="done" else "todo"; s.commit()
    elif d=="daily_new": context.user_data["awaiting_daily"]=True; await q.message.reply_text("Send task:")
    s.close()

async def daily_text(update, context):
    if not context.user_data.get("awaiting_daily"): return
    s=SessionLocal(); s.add(DailyTask(user_id=update.effective_user.id, text=update.message.text, date=date.today())); s.commit(); s.close()
    context.user_data["awaiting_daily"]=False; await update.message.reply_text("✅ Added")
