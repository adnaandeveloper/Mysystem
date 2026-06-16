from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User
import os

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admin only")
        return
    
    session = SessionLocal()
    try:
        users = session.query(User).all()
        text = f"⚙️ Admin Panel
Total users: {len(users)}

"
        for u in users:
            status = "✅" if u.is_allowed else "❌"
            admin = "👑" if u.is_admin else ""
            text += f"{status}{admin} {u.first_name} (@{u.username}) - ID:{u.telegram_id}
"
        
        keyboard = [
            [InlineKeyboardButton("➕ Approve User", callback_data="adm_approve")],
            [InlineKeyboardButton("➖ Remove User", callback_data="adm_remove")]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        session.close()

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "adm_approve":
        context.user_data["awaiting"] = "admin_approve"
        await query.message.reply_text("Send Telegram ID to approve:")
    elif query.data == "adm_remove":
        context.user_data["awaiting"] = "admin_remove"
        await query.message.reply_text("Send Telegram ID to remove:")

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("awaiting")
    if not state or not state.startswith("admin_"):
        return
    
    try:
        uid = int(update.message.text.strip())
    except:
        await update.message.reply_text("Invalid ID")
        return
    
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=uid).first()
        if not user:
            await update.message.reply_text("User not found. They must /start first.")
            return
        
        if state == "admin_approve":
            user.is_allowed = True
            session.commit()
            await update.message.reply_text(f"✅ Approved {user.first_name}")
        elif state == "admin_remove":
            user.is_allowed = False
            session.commit()
            await update.message.reply_text(f"❌ Removed {user.first_name}")
        
        context.user_data["awaiting"] = None
    finally:
        session.close()
