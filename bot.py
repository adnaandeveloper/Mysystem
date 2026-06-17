import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from db import Base, engine
from handlers.start import start_handler
from handlers.menu import menu_router
from handlers.today import today_callback
from handlers.plan import plan_handler
from handlers.habits import habits_callback, habits_recurrence, habits_day
from handlers.admin import admin_callback

TOKEN = os.getenv("TELEGRAM_TOKEN")

def main():
    Base.metadata.create_all(bind=engine)
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    
    # callbacks - specific first
    app.add_handler(CallbackQueryHandler(today_callback, pattern="^td_"))
    app.add_handler(CallbackQueryHandler(plan_handler, pattern="^pick_"))
    app.add_handler(CallbackQueryHandler(habits_callback, pattern="^hb_"))
    app.add_handler(CallbackQueryHandler(habits_callback, pattern="^hbd_"))
    app.add_handler(CallbackQueryHandler(habits_recurrence, pattern="^hr_"))
    app.add_handler(CallbackQueryHandler(habits_day, pattern="^day_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))

    app.add_handler(CallbackQueryHandler(habits_callback, pattern="^hview_"))
app.add_handler(CallbackQueryHandler(habits_callback, pattern="^hdel_"))
    
    # remove this line - you don't have a back_ callback
    # app.add_handler(CallbackQueryHandler(today_callback, pattern="^back_"))

    # text messages last
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_router))

    print("Bot started successfully")
    app.run_polling()

if __name__ == "__main__":
    main()