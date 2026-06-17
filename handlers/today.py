from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import TodayItem, User, BacklogItem, DoneItem, HistoryLog
from handlers.start import get_main_keyboard, ADMIN_ID

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user_id = update.effective_user.id
        user = session.query(User).filter_by(telegram_id=user_id).first()
        items = session.query(TodayItem).filter_by(user_id=user.id, done=False).all()

        if not items:
            text = "✅ Today is empty - all done!"
            keyboard = []
        else:
            text = f"Today ({len(items)} tasks)\nTap to complete:"
            keyboard = [[InlineKeyboardButton(f"• {i.text[:50]}", callback_data=f"td_done_{i.id}")] for i in items]

        keyboard.append([InlineKeyboardButton("➕ Pick from Backlog", callback_data="td_pick")])
        keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_menu")])

        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        session.close()

async def today_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()

        if data.startswith("td_done_"):
            item_id = int(data.split("_")[2])
            item = session.query(TodayItem).filter_by(id=item_id, user_id=user.id).first()
            if item:
                done = DoneItem(user_id=user.id, text=item.text)
                session.add(done)
                session.add(HistoryLog(user_id=user.id, action="today_done", detail=item.text))
                session.delete(item)
                session.commit()
                await today_handler(update, context)
                return

        elif data == "td_pick":
            items = session.query(BacklogItem).filter_by(user_id=user.id).all()
            if not items:
                await query.answer("Backlog empty", show_alert=True)
                return
            keyboard = [[InlineKeyboardButton(i.text[:40], callback_data=f"pick_{i.id}")] for i in items]
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_today")])
            await query.edit_message_text("Pick from Backlog:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "back_today":
            await today_handler(update, context)

        elif data == "back_menu":
            is_admin = update.effective_user.id == ADMIN_ID
            await query.message.delete()
            await update.message.reply_text("Menu:", reply_markup=get_main_keyboard(is_admin)) if hasattr(update, 'message') else await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Menu:",
                reply_markup=get_main_keyboard(is_admin)
            )
    finally:
        session.close()