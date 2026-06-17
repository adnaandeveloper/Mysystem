from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User, BacklogItem, TodayItem, DoneItem, Habit, HistoryLog
from handlers.start import ADMIN_ID, get_main_keyboard

def back_kb():
    return ReplyKeyboardMarkup([["⬅️ Back"]], resize_keyboard=True)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized")
        return

    keyboard = [
        [InlineKeyboardButton("👥 List Users", callback_data="adm_list")],
        [InlineKeyboardButton("✅ Approve User", callback_data="adm_approve")],
        [InlineKeyboardButton("❌ Remove User", callback_data="adm_remove")],
        [InlineKeyboardButton("🔥 RESET EVERYTHING", callback_data="adm_reset")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="adm_back")]
    ]
    await update.message.reply_text("Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if update.effective_user.id != ADMIN_ID:
        return

    session = SessionLocal()
    try:
        if data == "adm_list":
            users = session.query(User).all()
            text = f"Total users: {len(users)}\n\n"
            for u in users:
                status = "✅" if u.approved else "⏳"
                text += f"{status} {u.username or 'NoName'} (ID:{u.telegram_id})\n"
            await query.message.reply_text(text)

        elif data == "adm_approve":
            context.user_data["awaiting"] = "admin_approve"
            await query.message.reply_text("Send Telegram ID to approve:", reply_markup=back_kb())

        elif data == "adm_remove":
            context.user_data["awaiting"] = "admin_remove"
            await query.message.reply_text("Send Telegram ID to remove:", reply_markup=back_kb())

        elif data == "adm_reset":
            await query.message.reply_text("⚠️ Type YES to delete ALL data for ALL users", reply_markup=back_kb())
            context.user_data["awaiting"] = "admin_reset_confirm"

        elif data == "adm_back":
            await query.message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Menu:",
                reply_markup=get_main_keyboard(True)
            )
    finally:
        session.close()

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("awaiting")
    if not state or not state.startswith("admin_"):
        return

    session = SessionLocal()
    try:
        if state == "admin_approve":
            try:
                tid = int(update.message.text)
                user = session.query(User).filter_by(telegram_id=tid).first()
                if user:
                    user.approved = True
                    session.commit()
                    await update.message.reply_text(f"✅ Approved {tid}")
                else:
                    await update.message.reply_text("User not found")
            except:
                await update.message.reply_text("Invalid ID")

        elif state == "admin_remove":
            try:
                tid = int(update.message.text)
                user = session.query(User).filter_by(telegram_id=tid).first()
                if user and user.telegram_id != ADMIN_ID:
                    session.delete(user)
                    session.commit()
                    await update.message.reply_text(f"Removed {tid}")
                else:
                    await update.message.reply_text("Cannot remove admin")
            except:
                await update.message.reply_text("Invalid ID")

        elif state == "admin_reset_confirm":
            if update.message.text.strip().upper() == "YES":
                session.query(BacklogItem).delete()
                session.query(TodayItem).delete()
                session.query(DoneItem).delete()
                session.query(Habit).delete()
                session.query(HistoryLog).delete()
                session.query(User).filter(User.telegram_id != ADMIN_ID).delete()
                session.commit()
                await update.message.reply_text("✅ Everything reset. Only you remain.")
            else:
                await update.message.reply_text("Cancelled")

        context.user_data["awaiting"] = None
        await update.message.reply_text("Admin done", reply_markup=get_main_keyboard(True))
    finally:
        session.close()