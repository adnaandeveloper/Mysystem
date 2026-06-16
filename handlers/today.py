from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import TodayItem, User, BacklogItem, DoneItem, HistoryLog

async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        items = session.query(TodayItem).filter_by(user_id=user.id, done=False).all()
        
        if not items:
            text = "✅ Today is empty."
        else:
            text = "🎯 Today:
" + "
".join([f"{idx+1}. {i.text}" for idx, i in enumerate(items)])
        
        keyboard = []
        for i in items:
            keyboard.append([
                InlineKeyboardButton("✅ Done", callback_data=f"td_done_{i.id}"),
                InlineKeyboardButton("❌ Remove", callback_data=f"td_del_{i.id}")
            ])
        keyboard.append([InlineKeyboardButton("➕ Pick from Backlog", callback_data="td_pick")])
        
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
                await query.edit_message_text(f"✅ Completed: {item.text}")
        
        elif data.startswith("td_del_"):
            item_id = int(data.split("_")[2])
            item = session.query(TodayItem).filter_by(id=item_id, user_id=user.id).first()
            if item:
                session.delete(item)
                session.commit()
                await query.edit_message_text(f"Removed from Today")
        
        elif data == "td_pick":
            # Show backlog items to pick
            items = session.query(BacklogItem).filter_by(user_id=user.id).all()
            if not items:
                await query.message.reply_text("Backlog is empty. Add tasks first.")
                return
            keyboard = [[InlineKeyboardButton(i.text[:40], callback_data=f"pick_{i.id}")] for i in items]
            await query.message.reply_text("Select from Backlog:", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        session.close()
