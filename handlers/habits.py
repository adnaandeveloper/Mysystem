from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, HabitLog, ActionLog
from datetime import date

def log_action(user_id, action, details):
    s = SessionLocal()
    s.add(ActionLog(user_id=user_id, action=action, details=details))
    s.commit()
    s.close()

def is_due(habit):
    today = date.today()
    if habit.recurrence_type == "daily":
        return True
    if habit.recurrence_type in ["weekly","custom"] and habit.recurrence_days:
        days = [int(d) for d in habit.recurrence_days.split(",")]
        return today.weekday() in days
    if habit.recurrence_type == "yearly":
        return habit.recurrence_month == today.month and habit.recurrence_day == today.day
    return True

def get_streak(habit_id):
    s = SessionLocal()
    logs = s.query(HabitLog).filter_by(habit_id=habit_id, completed=True).order_by(HabitLog.date.desc()).all()
    s.close()
    streak = 0
    from datetime import timedelta
    today = date.today()
    for i, log in enumerate(logs):
        if log.date == today - timedelta(days=i):
            streak += 1
        else:
            break
    return streak

async def habits_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    habits = s.query(Habit).filter_by(user_id=update.effective_user.id, active=True).all()
    s.close()
    
    kb = [[InlineKeyboardButton("➕ Add Habit", callback_data="hb_add")]]
    for h in habits:
        if not is_due(h):
            continue
        s = SessionLocal()
        done = s.query(HabitLog).filter_by(habit_id=h.id, date=date.today(), completed=True).first()
        s.close()
        icon = "✅" if done else "⭕"
        streak = get_streak(h.id)
        kb.append([
            InlineKeyboardButton(f"{icon} {h.name} ({streak})", callback_data=f"hb_toggle_{h.id}"),
            InlineKeyboardButton("✏️", callback_data=f"hb_edit_{h.id}"),
            InlineKeyboardButton("🗑", callback_data=f"hb_del_{h.id}")
        ])
    
    text = "🔥 HABITS"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def habits_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    s = SessionLocal()
    
    if data == "hb_add":
        context.user_data["hb_step"] = "name"
        await q.message.reply_text("Send habit name:")
    elif data.startswith("hb_toggle_"):
        hid = int(data.split("_")[2])
        log = s.query(HabitLog).filter_by(habit_id=hid, date=date.today()).first()
        if not log:
            s.add(HabitLog(habit_id=hid, date=date.today(), completed=True))
            log_action(q.from_user.id, "habit_done", str(hid))
        else:
            log.completed = not log.completed
        s.commit()
    elif data.startswith("hb_del_"):
        hid = int(data.split("_")[2])
        h = s.query(Habit).get(hid)
        if h:
            s.delete(h)
            s.commit()
            log_action(q.from_user.id, "habit_delete", h.name)
    elif data.startswith("hb_edit_"):
        hid = int(data.split("_")[2])
        context.user_data["hb_edit"] = hid
        context.user_data["hb_step"] = "name"
        await q.message.reply_text("Send new name:")
    elif data.startswith("hb_type_"):
        htype = data.split("_")[2]
        hid = context.user_data.get("hb_new_id")
        h = s.query(Habit).get(hid)
        h.recurrence_type = htype
        if htype == "daily":
            s.commit()
            await q.message.reply_text("Habit saved")
        elif htype in ["weekly","custom"]:
            context.user_data["hb_step"] = "days"
            await q.message.reply_text("Send days numbers 0=Mon...6=Sun, comma separated (e.g. 0,3)")
            s.commit()
            s.close()
            return
        elif htype == "yearly":
            context.user_data["hb_step"] = "yearly"
            await q.message.reply_text("Send MM-DD (e.g. 12-25)")
            s.commit()
            s.close()
            return
        s.commit()
    
    s.close()
    await habits_handler(q, context)

async def habits_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "hb_step" not in context.user_data:
        return
    step = context.user_data["hb_step"]
    s = SessionLocal()
    
    if step == "name":
        if "hb_edit" in context.user_data:
            hid = context.user_data.pop("hb_edit")
            h = s.query(Habit).get(hid)
            h.name = update.message.text
            s.commit()
            s.close()
            context.user_data.pop("hb_step")
            await update.message.reply_text("Updated")
            await habits_handler(update, context)
            return
        else:
            h = Habit(user_id=update.effective_user.id, name=update.message.text)
            s.add(h)
            s.commit()
            context.user_data["hb_new_id"] = h.id
            context.user_data["hb_step"] = "type"
            s.close()
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Daily", callback_data="hb_type_daily")],
                [InlineKeyboardButton("Weekly", callback_data="hb_type_weekly")],
                [InlineKeyboardButton("Specific days", callback_data="hb_type_custom")],
                [InlineKeyboardButton("Yearly", callback_data="hb_type_yearly")]
            ])
            await update.message.reply_text("Choose recurrence:", reply_markup=kb)
            return
    elif step == "days":
        hid = context.user_data.get("hb_new_id")
        h = s.query(Habit).get(hid)
        h.recurrence_days = update.message.text
        s.commit()
        await update.message.reply_text("Habit saved")
    elif step == "yearly":
        hid = context.user_data.get("hb_new_id")
        h = s.query(Habit).get(hid)
        try:
            m,d = update.message.text.split("-")
            h.recurrence_month = int(m)
            h.recurrence_day = int(d)
            s.commit()
            await update.message.reply_text("Habit saved")
        except:
            await update.message.reply_text("Format error")
    s.close()
    context.user_data.pop("hb_step", None)
    context.user_data.pop("hb_new_id", None)
    await habits_handler(update, context)
