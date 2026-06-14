from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, HabitLog
from datetime import date, timedelta

def get_streak(habit_id):
    s = SessionLocal()
    logs = s.query(HabitLog).filter_by(habit_id=habit_id, completed=True).order_by(HabitLog.date.desc()).all()
    s.close()
    streak = 0
    today = date.today()
    for log in logs:
        if log.date == today - timedelta(days=streak):
            streak += 1
        else: break
    return streak

async def habit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    habits = s.query(Habit).filter_by(user_id=update.effective_user.id, active=True).all()
    s.close()

    text = "🔥 Habits:\n\n" + "\n".join([f"{h.name} — {get_streak(h.id)} day streak" for h in habits]) or "No habits yet"

    kb = [[InlineKeyboardButton("➕ Add Habit", callback_data="habit_add")]]
    for h in habits:
        kb.append([
            InlineKeyboardButton(f"✅ {h.name[:15]}", callback_data=f"habit_done_{h.id}"),
            InlineKeyboardButton("✏️", callback_data=f"habit_edit_{h.id}"),
            InlineKeyboardButton("🗑", callback_data=f"habit_del_{h.id}"),
        ])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def habit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()

    if q.data == "habit_add":
        context.user_data["awaiting"] = "habit_add"
        await q.message.reply_text("Send habit name:")

    elif q.data.startswith("habit_done_"):
        hid = int(q.data.split("_")[2])
        log = s.query(HabitLog).filter_by(habit_id=hid, date=date.today()).first()
        if not log:
            s.add(HabitLog(habit_id=hid, date=date.today(), completed=True))
        else:
            log.completed = not log.completed
        s.commit()
        await q.answer("Logged!")

    elif q.data.startswith("habit_edit_"):
        hid = int(q.data.split("_")[2])
        context.user_data["awaiting"] = f"habit_edit_{hid}"
        await q.message.reply_text("Send new name:")

    elif q.data.startswith("habit_del_"):
        hid = int(q.data.split("_")[2])
        h = s.query(Habit).get(hid)
        if h: s.delete(h); s.commit()

    s.close()
    await habit_handler(q, context)

# reuse backlog_text pattern - add to bot.py menu_router already calls it, so add this:
async def habit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting" not in context.user_data: return
    action = context.user_data.pop("awaiting")
    s = SessionLocal()
    if action == "habit_add":
        s.add(Habit(user_id=update.effective_user.id, name=update.message.text))
        s.commit()
        await update.message.reply_text("Habit added")
    elif action.startswith("habit_edit_"):
        hid = int(action.split("_")[2])
        h = s.query(Habit).get(hid)
        if h: h.name = update.message.text; s.commit()
        await update.message.reply_text("Updated")
    s.close()