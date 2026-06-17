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
        user_id = update.effective_user.id
        user = session.query(User).filter_by(telegram_id=user_id).first()
        all_habits = session.query(Habit).filter_by(user_id=user.id).all()

        today = datetime.utcnow()
        weekday = today.strftime("%A")
        is_weekday = weekday in ["Monday","Tuesday","Wednesday","Thursday","Friday"]

        due_habits = []
        for h in all_habits:
            if h.last_done and h.last_done.date() == today.date():
                continue
            if h.recurrence == "daily":
                due_habits.append(h)
            elif h.recurrence == "weekdays" and is_weekday:
                due_habits.append(h)
            elif h.recurrence.startswith("weekly-"):
                day = h.recurrence.split("-")[1]
                if day == weekday:
                    due_habits.append(h)

        keyboard = []
        if due_habits:
            for h in due_habits:
                keyboard.append([InlineKeyboardButton(f"☐ {h.name}", callback_data=f"hbd_{h.id}")])
            text = f"Habits for {weekday} - tap to complete:"
        else:
            text = "✅ All habits done for today!"

        keyboard.append([InlineKeyboardButton("➕ Add Habit", callback_data="hb_add")])
        keyboard.append([InlineKeyboardButton("📋 View All Habits", callback_data="hb_all")])

        # works for both message and callback
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            await update.message.reply_text("Press Back to return", reply_markup=back_kb())
    finally:
        session.close()

async def habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()

        if data == "hb_add":
            context.user_data["awaiting"] = "habit_name"
            await query.message.reply_text("Send habit name:", reply_markup=back_kb())
            return

        if data == "hb_all":
            habits = session.query(Habit).filter_by(user_id=user.id).all()
            if not habits:
                await query.message.reply_text("No habits yet")
                return
            text = "All Habits:\n"
            for h in habits:
                text += f"\n• {h.name} ({h.recurrence}) streak:{h.streak}"
            await query.message.reply_text(text)
            return

        if data.startswith("hbd_"):
            hid = int(data.split("_")[1])
            habit = session.query(Habit).filter_by(id=hid).first()
            if habit:
                habit.streak += 1
                habit.last_done = datetime.utcnow()
                session.add(HistoryLog(user_id=habit.user_id, action="habit_done", detail=habit.name))
                session.commit()
                await query.answer(f"Done: {habit.name}")
                # refresh - habit disappears for today
                await habits_handler(update, context)
            return
    finally:
        session.close()

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