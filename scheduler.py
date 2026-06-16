from apscheduler.schedulers.background import BackgroundScheduler

def setup_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.start()
