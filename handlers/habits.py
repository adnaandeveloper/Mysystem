from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, User, HistoryLog
from datetime import datetime

def back_keyboard():
    return ReplyKeyboardMarkup([["⬅️ Back"]], resize_keyboard=True)

async def habits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        habits = session.query(Habit).filter_by(user_id=user.id).all()

        if not habits:
            text = "No habits yet."
        else:
            text = "Habits:"
            for h in habits:
                text += f"\n- {h.name} ({h.recurrence}) streak: {h.streak}"

        keyboard = [
            [InlineKeyboardButton("Add Habit", callback_data="hb_add")],
            [InlineKeyboardButton("Mark Done", callback_data="hb_done")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        await update.message.reply_text("Or press Back", reply_markup=back_keyboard())
    finally:
        session.close()

async def habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "hb_add":
        context.user_data["awaiting"] = "habit_name"
        await query.message.reply_text("Send habit name:", reply_markup=back_keyboard())
    elif query.data == "hb_done":
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
            habits = session.query(Habit).filter_by(user_id=user.id).all()
            if not habits:
                await query.message.reply_text("No habits")
                return
            keyboard = [[InlineKeyboardButton(h.name, callback_data=f"hbd_{h.id}")] for h in habits]
            await query.message.reply_text("Which habit done?", reply_markup=InlineKeyboardMarkup(keyboard))
        finally:
            session.close()
    elif query.data.startswith("hbd_"):
        hid = int(query.data.split("_")[1])
        session = SessionLocal()
        try:
            habit = session.query(Habit).filter_by(id=hid).first()
            habit.streak += 1
            habit.last_done = datetime.utcnow()
            session.add(HistoryLog(user_id=habit.user_id, action="habit_done", detail=habit.name))
            session.commit()
            await query.message.reply_text(f"{habit.name} done! Streak: {habit.streak}")
        finally:
            session.close()

async def habits_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("awaiting")
    if state == "habit_name":
        context.user_data["habit_name"] = update.message.text
        context.user_data["awaiting"] = "habit_recurrence"
        keyboard = [
            [InlineKeyboardButton("Daily", callback_data="hr_daily")],
            [InlineKeyboardButton("Weekly", callback_data="hr_weekly")],
            [InlineKeyboardButton("Mon-Fri", callback_data="hr_weekdays")]
        ]
        await update.message.reply_text("Choose recurrence:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

async def habits_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    rec = query.data.split("_")[1]
    name = context.user_data.get("habit_name")

    if rec == "weekly":
        context.user_data["awaiting"] = "habit_day"
        keyboard = [[InlineKeyboardButton(d, callback_data=f"day_{d}")] for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]]
        await query.message.reply_text("Which day?", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        habit = Habit(user_id=user.id, name=name, recurrence=rec)
        session.add(habit)
        session.commit()
        context.user_data["awaiting"] = None
        context.user_data["habit_name"] = None
        await query.message.reply_text(f"Habit added: {name} ({rec})")
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
        await query.message.reply_text(f"Habit added: {name} every {day}")
    finally:
        session.close()