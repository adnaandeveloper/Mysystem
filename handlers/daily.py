from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DailyTask, BacklogItem
from datetime import date

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    uid = update.effective_user.id
    tasks = s.query(DailyTask).filter_by(user_id=uid, date=date.today()).filter(DailyTask.status!= "done").all()
    s.close()

    if not tasks:
        text = "✅ Today is empty"
    else:
        text = "✅ Today:"

    kb = []
    for t in tasks:
        # Row 1: the task (tap to toggle done)
        kb.append([InlineKeyboardButton(f"○ {t.text}", callback_data=f"done_{t.id}")])
        # Row 2: X button to delete (returns to backlog automatically)
        kb.append([InlineKeyboardButton("✖️ Remove", callback_data=f"del_{t.id}")])

    kb.append([InlineKeyboardButton("📚 View All Done", callback_data="view_done")])
    kb.append([InlineKeyboardButton("➕ Add manual", callback_data="add_manual")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).all()
    s.close()
    kb = [[InlineKeyboardButton(i.text, callback_data=f"pick_{i.id}")] for i in items[:20]]
    await update.message.reply_text("🗓 Tap to add to Today:", reply_markup=InlineKeyboardMarkup(kb))

async def done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    done = s.query(DailyTask).filter_by(user_id=update.effective_user.id, status="done").order_by(DailyTask.date.desc()).limit(30).all()
    s.close()
    text = "📚 Done Tasks:\n\n" + "\n".join([f"✓ {d.date} - {d.text}" for d in done]) or "None yet"
    await update.message.reply_text(text)

async def daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()
    uid = q.from_user.id

    if q.data.startswith("pick_"):
        bid = int(q.data.split("_")[1])
        exists = s.query(DailyTask).filter_by(user_id=uid, backlog_id=bid, date=date.today()).first()
        if not exists:
            item = s.query(BacklogItem).get(bid)
            s.add(DailyTask(user_id=uid, backlog_id=bid, text=item.text, date=date.today(), status="todo"))
            s.commit()
            await q.answer("Added to Today")

    elif q.data.startswith("done_"):
        tid = int(q.data.split("_")[1])
        t = s.query(DailyTask).get(tid)
        if t:
            t.status = "done"
            s.commit()

    elif q.data.startswith("del_"):
        tid = int(q.data.split("_")[1])
        t = s.query(DailyTask).get(tid)
        if t:
            s.delete(t) # backlog item stays, so it's "back to backlog"
            s.commit()

    elif q.data == "view_done":
        await done_handler(q, context)
        s.close()
        return

    elif q.data == "add_manual":
        context.user_data["awaiting"] = "daily_add"
        await q.message.reply_text("Send task text:")

    s.close()
    await today_handler(q, context)

async def daily_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting")!= "daily_add":
        return
    context.user_data.pop("awaiting")
    s = SessionLocal()
    s.add(DailyTask(user_id=update.effective_user.id, text=update.message.text, date=date.today(), status="todo"))
    s.commit()
    s.close()
    await update.message.reply_text("Added")