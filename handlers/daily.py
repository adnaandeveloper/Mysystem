from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import DailyTask, BacklogItem
from datetime import date

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    tasks = s.query(DailyTask).filter_by(user_id=update.effective_user.id, date=date.today()).all()
    s.close()

    if not tasks:
        text = "✅ No tasks for today. Use 🗓 Plan to pick from backlog."
    else:
        text = "✅ Today:\n\n" + "\n".join([f"{'✓' if t.status=='done' else '○'} {t.text}" for t in tasks])

    kb = [[InlineKeyboardButton("➕ Add manual", callback_data="daily_add")]]
    for t in tasks:
        kb.append([
            InlineKeyboardButton("✓" if t.status!="done" else "↩️", callback_data=f"daily_toggle_{t.id}"),
            InlineKeyboardButton("✏️", callback_data=f"daily_edit_{t.id}"),
            InlineKeyboardButton("🗑", callback_data=f"daily_del_{t.id}"),
        ])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).limit(20).all()
    s.close()

    kb = [[InlineKeyboardButton(i.text[:30], callback_data=f"pick_{i.id}")] for i in items]
    await update.message.reply_text("🗓 Pick 3 for today from backlog:", reply_markup=InlineKeyboardMarkup(kb))

async def daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()
    uid = q.from_user.id

    if q.data.startswith("pick_"):
        bid = int(q.data.split("_")[1])
        item = s.query(BacklogItem).get(bid)
        if item:
            s.add(DailyTask(user_id=uid, backlog_id=bid, text=item.text, date=date.today()))
            s.commit()
            await q.answer(f"Added: {item.text}")

    elif q.data.startswith("daily_toggle_"):
        tid = int(q.data.split("_")[2])
        t = s.query(DailyTask).get(tid)
        if t: t.status = "done" if t.status!="done" else "todo"; s.commit()

    elif q.data.startswith("daily_del_"):
        tid = int(q.data.split("_")[2])
        t = s.query(DailyTask).get(tid)
        if t: s.delete(t); s.commit()

    elif q.data == "daily_add":
        context.user_data["awaiting"] = "daily_add"
        await q.message.reply_text("Send task text:")

    elif q.data.startswith("daily_edit_"):
        tid = int(q.data.split("_")[2])
        context.user_data["awaiting"] = f"daily_edit_{tid}"
        await q.message.reply_text("Send new text:")

    s.close()
    # refresh view
    await today_handler(q, context)

async def daily_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting" not in context.user_data: return
    action = context.user_data.pop("awaiting")
    s = SessionLocal()

    if action == "daily_add":
        s.add(DailyTask(user_id=update.effective_user.id, text=update.message.text, date=date.today()))
        s.commit()
        await update.message.reply_text("Added to Today")

    elif action.startswith("daily_edit_"):
        tid = int(action.split("_")[2])
        t = s.query(DailyTask).get(tid)
        if t: t.text = update.message.text; s.commit()
        await update.message.reply_text("Updated")

    s.close()