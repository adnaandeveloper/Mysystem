from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User
import os
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
def get_main_keyboard(is_admin=False):
    rows = [["📥 Backlog", "✅ Today"],["🔥 Habits", "📦 All Tasks"],["📜 History"]]
    if is_admin:
        rows.append(["⚙️ Admin"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = SessionLocal()
    try:
        db_user = session.query(User).filter_by(telegram_id=user.id).first()
        is_admin = user.id == ADMIN_ID
        if not db_user:
            db_user = User(telegram_id=user.id, username=user.username, first_name=user.first_name, is_admin=is_admin, is_allowed=is_admin)
            session.add(db_user)
        else:
            if is_admin and not db_user.is_admin:
                db_user.is_admin = True
                db_user.is_allowed = True
            if is_admin and not db_user.is_allowed:
                db_user.is_allowed = True
        session.commit()
        if not db_user.is_allowed and not is_admin:
            await update.message.reply_text("🚫 You don't have access yet. Ask admin to approve you.")
            return
        await update.message.reply_text(f"Welcome {user.first_name}! Use the menu below.", reply_markup=get_main_keyboard(is_admin))
    finally:
        session.close()
