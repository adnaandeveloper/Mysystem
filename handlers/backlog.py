from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import BacklogItem, DailyTask
from datetime import date

async def backlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = SessionLocal()
    items = s.query(BacklogItem).filter_by(user_id=update.effective_user.id, archived=False).order_by(BacklogItem.id.desc()).all()
    s.close()

    if not items:
        text = "📥 Backlog is empty"
    else:
        text = "📥 Your Backlog:\n\n" + "\n".join([f"{i.id}. {i.text}" for i in items[:15]])

    kb = [
        [InlineKeyboardButton("➕ Add New", callback_data="backlog_add")],
    ]
    for i in items[:10]:
        kb.append([
            InlineKeyboardButton(f"✏️ {i.id}", callback_data=f"backlog_edit_{i.id}"),
            InlineKeyboardButton(f"📅 Pick", callback_data=f"backlog_pick_{i.id}"),
            InlineKeyboardButton(f"🗄 Archive", callback_data=f"backlog_archive_{i.id}"),
            InlineKeyboardButton(f"🗑 Delete", callback_data=f"backlog_del_{i.id}"),
        ])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def backlog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    s = SessionLocal()
    uid = q.from_user.id

    if data == "backlog_add":
        context.user_data["awaiting"] = "backlog_add"
        await q.message.reply_text("Send the idea text:")

    elif data.startswith("backlog_edit_"):
        bid = int(data.split("_")[2])
        context.user_data["awaiting"] = f"backlog_edit_{bid}"
        item = s.query(BacklogItem).get(bid)
        await q.message.reply_text(f"Editing: {item.text}\nSend new text:")

    elif data.startswith("backlog_archive_"):
        bid = int(data.split("_")[2])
        item = s.query(BacklogItem).get(bid)
        if item and item.user_id == uid:
            item.archived = True
            s.commit()
        await q.message.edit_text("Archived ✅")

    elif data.startswith("backlog_del_"):
        bid = int(data.split("_")[2])
        item = s.query(BacklogItem).get(bid)
        if item and item.user_id == uid:
            s.delete(item)
            s.commit()
        await q.message.edit_text("Deleted 🗑")

    elif data.startswith("backlog_pick_"):
        bid = int(data.split("_")[2])
        item = s.query(BacklogItem).get(bid)
        if item:
            # create today's task
            exists = s.query(DailyTask).filter_by(user_id=uid, backlog_id=bid, date=date.today()).first()
            if not exists:
                s.add(DailyTask(user_id=uid, backlog_id=bid, text=item.text, date=date.today()))
                s.commit()
            await q.message.reply_text(f"Added to Today: {item.text}")

    s.close()

async def backlog_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting" not in context.user_data:
        return
    action = context.user_data.pop("awaiting")
    s = SessionLocal()

    if action == "backlog_add":
        s.add(BacklogItem(user_id=update.effective_user.id, text=update.message.text))
        s.commit()
        await update.message.reply_text("Added to backlog ✅")

    elif action.startswith("backlog_edit_"):
        bid = int(action.split("_")[2])
        item = s.query(BacklogItem).get(bid)
        if item:
            item.text = update.message.text
            s.commit()
            await update.message.reply_text("Updated ✏️")

    s.close()