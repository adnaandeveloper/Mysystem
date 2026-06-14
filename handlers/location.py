from telegram import Update
from telegram.ext import ContextTypes
import requests
from db import SessionLocal
from models import User

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    try:
        # free API, no key needed
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={loc.latitude}&longitude={loc.longitude}&localityLanguage=en"
        resp = requests.get(url, timeout=5)
        tz = resp.json().get("timezone", "Europe/Copenhagen")
    except:
        tz = "Europe/Copenhagen"
    
    s = SessionLocal()
    u = s.query(User).filter_by(telegram_id=update.effective_user.id).first()
    if u:
        u.timezone = tz
        s.commit()
        await update.message.reply_text(f"Timezone updated to {tz}")
    s.close()