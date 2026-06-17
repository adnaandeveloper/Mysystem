from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, User, HistoryLog
from datetime import datetime

def back_kb():
    return ReplyKeyboardMarkup([["⬅️ Back"]], resize_keyboard=True)

async def habits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        habits = session.query(Habit).filter_by(user_id=user.id).all()

        if not habits:
            await update.message.reply_text("No habits yet.", reply_markup=back_kb())
            keyboard = [[InlineKeyboardButton("➕ Add Habit", callback_data="hb_add")]]
            await update.message.reply_text("Add your first habit:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        keyboard = []
        for h in habits:
            keyboard.append([InlineKeyboardButton(f"{h.name} ({h.streak})", callback_data=f"hview_{h.id}")])
        keyboard.append([InlineKeyboardButton("➕ Add Habit", callback_data="hb_add")])
        await update.message.reply_text("Your Habits - tap to open:", reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("Press Back to return", reply_markup=back_kb())
    finally:
        session.close()

async def habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "hb_add":
        context.user_data["awaiting"] = "habit_name"
        await query.message.reply_text("Send habit name:", reply_markup=back_kb())
        return

    if data.startswith("hview_"):
        hid = int(data.split("_")[1])
        session = SessionLocal()
        try:
            h = session.query(Habit).filter_by(id=hid).first()
            if not h:
                await query.message.reply_text("Habit not found")
                return
            kb = [
                [InlineKeyboardButton("✅ Mark Done", callback_data=f"hbd_{h.id}")],
                [InlineKeyboardButton("❌ Delete Habit", callback_data=f"hdel_{h.id}")]
            ]
            text = f"{h.name}\nRecurrence: {h.recurrence}\nCurrent Streak: {h.streak}"
            if h.last_done:
                text += f"\nLast done: {h.last_done.strftime('%Y-%m-%d')}"
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        finally:
            session.close()
        return

    if data.startswith("hbd_"):
        hid = int(data.split("_")[1])
        session = SessionLocal()
        try:
            habit = session.query(Habit).filter_by(id=hid).first()
            if habit:
                habit.streak += 1
                habit.last_done = datetime.utcnow()
                session.add(HistoryLog(user_id=habit.user_id, action="habit_done", detail=habit.name))
                session.commit()
                await query.message.reply_text(f"✅ {habit.name} marked done!\nNew streak: {habit.streak}")
                await habits_handler(query, context)
        finally:
            session.close()
        return

    if data.startswith("hdel_"):
        hid = int(data.split("_")[1])
        session = SessionLocal()
        try:
            h = session.query(Habit).filter_by(id=hid).first()
            if h:
                session.delete(h)
                session.commit()
                await query.message.reply_text(f"Deleted habit: {h.name}")
                await habits_handler(query, context)
        finally:
            session.close()
        return

async def habits_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("awaiting")
    if state!= "habit_name":
        return
    context.user_data["habit_name"] = update.message.text
    context.user_data["awaiting"] = "habit_recurrence"
    keyboard = [
        [InlineKeyboardButton("Daily", callback_data="hr_daily")],
        [InlineKeyboardButton("Weekly", callback_data="hr_weekly")],
        [InlineKeyboardButton("Mon-Fri", callback_data="hr_weekdays")]
    ]
    await update.message.reply_text("Choose recurrence:", reply_markup=InlineKeyboardMarkup(keyboard))

async def habits_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec = query.data.split("_")[1]
    name = context.user_data.get("habit_name")

    if rec == "weekly":
        context.user_data["awaiting"] = "habit_day"
        keyboard = [[InlineKeyboardButton(d, callback_data=f"day_{d}")] for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]]
        await query.message.reply_text("Which day of week?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        habit = Habit(user_id=user.id, name=name, recurrence=rec)
        session.add(habit)
        session.commit()
        context.user_data["awaiting"] = None
        context.user_data.pop("habit_name", None)
        await query.message.reply_text(f"✅ Habit added: {name} ({rec})")
        await habits_handler(query, context)
    finally:
        session.close()

async def habits_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data.split("_")[1]
    name = context.user_data.get("habit_name")
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        habit = Habit(user_id=user.id, name=name, recurrence=f"weekly-{day}")
        session.add(habit)
        session.commit()
        context.user_data["awaiting"] = None
        context.user_data.pop("habit_name", None)
        await query.message.reply_text(f"✅ Habit added: {name} every {day}")
        await habits_handler(query, context)
    finally:
        session.close()