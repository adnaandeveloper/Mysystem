import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = SessionLocal()
    db_user = session.query(User).filter_by(telegram_id=user.id).first()
    if not db_user:
        is_admin = user.id == ADMIN_ID
        db_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            is_admin=is_admin,
            is_allowed=is_admin,
            timezone=os.getenv("TZ_DEFAULT", "Europe/Copenhagen")
        )
        session.add(db_user)
        session.commit()
    if not db_user.is_allowed and not db_user.is_admin:
        await update.message.reply_text("Not authorized")
        session.close()
        return
    kb = ReplyKeyboardMarkup([[KeyboardButton("Update timezone", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
    msg = f"Welcome {user.first_name}!\nCurrent timezone: {db_user.timezone}\n\n/backlog /plan /today /habit"
    await update.message.reply_text(msg, reply_markup=kb)
    session.close()
