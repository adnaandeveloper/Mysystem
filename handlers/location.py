from telegram import Update
from telegram.ext import ContextTypes
from timezonefinder import TimezoneFinder
from db import SessionLocal
from models import User

tf = TimezoneFinder()

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    tz = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
    if not tz:
        return
    s = SessionLocal()
    u = s.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if u:
        u.timezone = tz
        s.commit()
        await update.message.reply_text(f"Timezone updated to {tz}")
    s.close()
