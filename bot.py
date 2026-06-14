import os, logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from db import engine
from models import Base
from handlers.start import start_handler
from handlers.backlog import backlog_handler, backlog_callback, backlog_text
from handlers.daily import today_handler, plan_handler, daily_callback, daily_text
from handlers.habits import habit_handler, habit_callback, habit_text
from handlers.admin import admin_handler, admin_callback, admin_text
from handlers.location import location_handler
from scheduler import setup_scheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📥 Backlog":
        await backlog_handler(update, context)
    elif text == "🗓 Plan":
        await plan_handler(update, context)
    elif text == "✅ Today":
        await today_handler(update, context)
    elif text == "🔥 Habit":
        await habit_handler(update, context)
    elif text == "📍 Update timezone":
        await update.message.reply_text("Share location")
    else:
        await backlog_text(update, context)
        await habit_text(update, context)
        await daily_text(update, context)
        await admin_text(update, context)

def main():
    Base.metadata.create_all(bind=engine)
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("backlog", backlog_handler))
    app.add_handler(CommandHandler("today", today_handler))
    app.add_handler(CommandHandler("plan", plan_handler))
    app.add_handler(CommandHandler("habit", habit_handler))
    app.add_handler(CommandHandler("admin", admin_handler))
    
    app.add_handler(CallbackQueryHandler(backlog_callback, pattern=r"^backlog_"))
    app.add_handler(CallbackQueryHandler(daily_callback, pattern=r"^(pick_|daily_)"))
    app.add_handler(CallbackQueryHandler(habit_callback, pattern=r"^habit_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^admin_"))
    
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))
    
    setup_scheduler(app)
    app.run_polling()

if __name__ == "__main__":
    main()