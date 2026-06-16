import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    s = SessionLocal()
    db_user = s.query(User).filter_by(telegram_id=user.id).first()
    
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
        s.add(db_user)
        s.commit()
    
    if not db_user.is_allowed and not db_user.is_admin:
        await update.message.reply_text("⛔ Not authorized. Ask admin to add you.")
        s.close()
        return

    # Build keyboard
    keyboard = [
        [KeyboardButton("📥 Backlog"), KeyboardButton("✅ Today")],
        [KeyboardButton("🔥 Habits"), KeyboardButton("📚 All Tasks")],
        [KeyboardButton("🕒 History")]
    ]
    if db_user.is_admin:
        keyboard.append([KeyboardButton("⚙️ Admin")])
    
    await update.message.reply_text(
        f"Welcome {user.first_name}!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    )
    s.close()
