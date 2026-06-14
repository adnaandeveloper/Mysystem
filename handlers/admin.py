import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User
ADMIN_ID=int(os.getenv("ADMIN_ID","0"))

async def admin_handler(update, context):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text("Admin only"); return
    kb=[[InlineKeyboardButton("👥 List", callback_data="admin_list")],[InlineKeyboardButton("➕ Add", callback_data="admin_add")]]
    await update.message.reply_text("Admin", reply_markup=InlineKeyboardMarkup(kb))

async def admin_callback(update, context):
    q=update.callback_query; await q.answer(); s=SessionLocal()
    if q.data=="admin_list": us=s.query(User).all(); await q.message.reply_text("
".join([f"{u.telegram_id} {u.timezone}" for u in us]))
    elif q.data=="admin_add": context.user_data["admin_action"]="add"; await q.message.reply_text("Send ID")
    s.close()

async def admin_text(update, context):
    if update.effective_user.id!=ADMIN_ID or not context.user_data.get("admin_action"): return
    uid=int(update.message.text); s=SessionLocal(); u=s.query(User).filter_by(telegram_id=uid).first()
    if not u: u=User(telegram_id=uid, is_allowed=True); s.add(u)
    else: u.is_allowed=True
    s.commit(); s.close(); await update.message.reply_text("Allowed"); context.user_data["admin_action"]=None
