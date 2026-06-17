from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, User, HistoryLog

def back_keyboard():
    return ReplyKeyboardMarkup([["⬅️ Back"]], resize_keyboard=True)

async def backlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting"] = "backlog_add"
    await update.message.reply_text(
        "Send tasks to Backlog. One per message.\nType /done or press Back when finished:",
        reply_markup=back_keyboard()
    )

async def backlog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting")!= "backlog_add":
        return

    text = update.message.text
    if text == "⬅️ Back" or text == "/done":
        context.user_data["awaiting"] = None
        from handlers.start import get_main_keyboard, ADMIN_ID
        is_admin = update.effective_user.id == ADMIN_ID
        await update.message.reply_text("Back to menu", reply_markup=get_main_keyboard(is_admin))
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        item = BacklogItem(user_id=user.id, text=text)
        session.add(item)
        session.add(HistoryLog(user_id=user.id, action="backlog_add", detail=text))
        session.commit()
        await update.message.reply_text(f"Added: {text}\nSend next, or Back to finish.")
    finally:
        session.close()