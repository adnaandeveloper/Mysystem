from telegram import Update
from telegram.ext import ContextTypes
from handlers.backlog import backlog_handler, backlog_text
from handlers.today import today_handler
from handlers.habits import habits_handler, habits_text
from handlers.done import done_handler
from handlers.history import history_handler
from handlers.admin import admin_handler, admin_text
from handlers.start import get_main_keyboard, ADMIN_ID
from db import SessionLocal
from models import User
from handlers.done_today import done_today_handler

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # GLOBAL BACK - works from anywhere
    if text in ["⬅ Back", "⬅️ Back"]:  # <-- accept both versions
        context.user_data["awaiting"] = None
        context.user_data.pop("habit_name", None)
        is_admin = user.id == ADMIN_ID
        await update.message.reply_text("Menu:", reply_markup=get_main_keyboard(is_admin))
        return

    session = SessionLocal()
    try:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        if not db_user or (not db_user.is_allowed and user.id != ADMIN_ID):
            context.user_data["awaiting"] = None
            await update.message.reply_text("Not allowed.")
            return

        state = context.user_data.get("awaiting")

        if state:
            if state == "backlog_add":
                return await backlog_text(update, context)
            if state in ["habit_name", "habit_recurrence", "habit_day"]:
                return await habits_text(update, context)
            if state.startswith("admin_"):
                return await admin_text(update, context)

        # Clear state when clicking main menu
        context.user_data["awaiting"] = None

        if text == "Backlog":
            return await backlog_handler(update, context)
        elif text == "Today":
            return await today_handler(update, context)
        elif text == "Habits":
            return await habits_handler(update, context)
        elif text == "All Tasks":
            return await done_handler(update, context)
        elif text == "History":
            return await history_handler(update, context)
        elif text == "Admin":
            return await admin_handler(update, context)
        elif text == "Done Today":  # <-- FIXED: added return
            return await done_today_handler(update, context)
    finally:
        session.close()