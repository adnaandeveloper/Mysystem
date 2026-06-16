from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DailyTask, BacklogItem, ActionLog
from datetime import date

def log_action(user_id, action, details):
    s = SessionLocal()
    s.add(ActionLog(user_id=user_id, action=action, details=details))
    s.commit()
    s.close()

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    uid = update.effective_user.id
    tasks = s.query(DailyTask).filter_by(user_id=uid, date=date.today(), status="todo").all()
    s.close()
    
    kb = []
    for t in tasks:
        kb.append([InlineKeyboardButton(f"✓ {t.text}", callback_data=f"td_done_{t.id}")])
    kb.append([InlineKeyboardButton("➕ Pick from Backlog", callback_data="td_pick")])
    
    text = "✅ TODAY"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).all()
    s.close()
    kb = [[InlineKeyboardButton(i.text[:40], callback_data=f"td_pick_{i.id}")] for i in items]
    await update.message.reply_text("Pick tasks:", reply_markup=InlineKeyboardMarkup(kb))

async def all_tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    done = s.query(DailyTask).filter_by(user_id=update.effective_user.id, status="done").order_by(DailyTask.date.desc()).limit(100).all()
    s.close()
    text = "📚 COMPLETED:\n\n" + "\n".join([f"{d.date} - {d.text}" for d in done]) if done else "No tasks yet"
    await update.message.reply_text(text)

async def daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()
    uid = q.from_user.id
    
    if q.data == "td_pick":
        s.close()
        await plan_handler(q, context)
        return
    if q.data.startswith("td_pick_"):
        bid = int(q.data.split("_")[2])
        item = s.query(BacklogItem).get(bid)
        exists = s.query(DailyTask).filter_by(user_id=uid, backlog_id=bid, date=date.today()).first()
        if item and not exists:
            s.add(DailyTask(user_id=uid, backlog_id=bid, text=item.text, date=date.today()))
            s.commit()
            log_action(uid, "pick_today", item.text)
    elif q.data.startswith("td_done_"):
        tid = int(q.data.split("_")[2])
        t = s.query(DailyTask).get(tid)
        if t:
            t.status = "done"
            s.commit()
            log_action(uid, "complete_task", t.text)
    s.close()
    await today_handler(q, context)

async def daily_text(update, context):
    return
