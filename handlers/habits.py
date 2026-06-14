from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db import SessionLocal
from models import Habit, HabitLog
from datetime import date, timedelta

def streak(s, hid):
    logs = s.query(HabitLog).filter_by(habit_id=hid, completed=True).order_by(HabitLog.date.desc()).all()
    st=0; exp=date.today()
    for l in logs:
        if l.date==exp or (st==0 and l.date==exp-timedelta(days=1)): st+=1; exp=l.date-timedelta(days=1)
        else: break
    return st

async def habit_handler(update, context):
    s=SessionLocal(); uid=update.effective_user.id; args=context.args
    if args and args[0]=="add":
        name=" ".join(args[1:]); s.add(Habit(user_id=uid, name=name)); s.commit(); await update.message.reply_text(f"Added {name}"); s.close(); return
    hs=s.query(Habit).filter_by(user_id=uid, active=True).all()
    txt="🔥 Habits:
"; kb=[]
    for h in hs:
        txt+=f"{h.name} – {streak(s,h.id)}d
"; kb.append([InlineKeyboardButton(f"✅ {h.name}", callback_data=f"habit_done_{h.id}")])
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb)); s.close()

async def habit_callback(update, context):
    q=update.callback_query; await q.answer(); s=SessionLocal(); hid=int(q.data.split("_")[-1]); comp=q.data.startswith("habit_done")
    log=s.query(HabitLog).filter_by(habit_id=hid, date=date.today()).first()
    if not log: log=HabitLog(habit_id=hid, date=date.today(), completed=comp); s.add(log)
    else: log.completed=comp
    s.commit(); await q.message.reply_text("Logged"); s.close()
