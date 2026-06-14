import os
from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

async def admin_handler(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Admin OK")

async def admin_callback(update, context):
    pass

async def admin_text(update, context):
    pass
