from telegram import Update
from telegram.ext import ContextTypes
from timezonefinder import TimezoneFinder
from db import SessionLocal
from models import User

tf = TimezoneFinder()

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    if not loc:
        return
    
    tz_name = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    if not tz_name:
        await update.message.reply_text("❌ Could not detect timezone from location.")
        return
    
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if user:
        old_tz = user.timezone
        user.timezone = tz_name
        session.commit()
        await update.message.reply_text(
            f"🌍 Timezone updated!

"
            f"Before: {old_tz}
"
            f"Now: {tz_name}

"
            f"Your 7:30 AM prompt will now follow local time. Share location again anytime you travel."
        )
    session.close()
