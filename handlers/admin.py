from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User, ActionLog

def log_action(user_id, action, details):
    s = SessionLocal()
    s.add(ActionLog(user_id=user_id, action=action, details=details))
    s.commit()
    s.close()

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    user = s.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if not user or not user.is_admin:
        await update.message.reply_text("Not authorized")
        s.close()
        return
    users = s.query(User).all()
    s.close()
    kb = [[InlineKeyboardButton(f"{'✅' if u.is_allowed else '❌'} {u.first_name} ({u.telegram_id})", callback_data=f"adm_toggle_{u.id}")] for u in users]
    kb.append([InlineKeyboardButton("➕ Add User", callback_data="adm_add")])
    await update.message.reply_text("⚙️ ADMIN", reply_markup=InlineKeyboardMarkup(kb))

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    s = SessionLocal()
    if q.data.startswith("adm_toggle_"):
        uid = int(q.data.split("_")[2])
        u = s.query(User).get(uid)
        u.is_allowed = not u.is_allowed
        s.commit()
        log_action(q.from_user.id, "toggle_user", str(uid))
    elif q.data == "adm_add":
        context.user_data["adm_add"] = True
        await q.message.reply_text("Send Telegram ID to add:")
        s.close()
        return
    s.close()
    await admin_handler(q, context)

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("adm_add"):
        return
    context.user_data.pop("adm_add")
    try:
        tid = int(update.message.text)
        s = SessionLocal()
        u = s.query(User).filter_by(telegram_id=tid).first()
        if not u:
            u = User(telegram_id=tid, is_allowed=True, first_name="User")
            s.add(u)
        else:
            u.is_allowed = True
        s.commit()
        s.close()
        log_action(update.effective_user.id, "add_user", str(tid))
        await update.message.reply_text("User added")
    except:
        await update.message.reply_text("Invalid ID")
