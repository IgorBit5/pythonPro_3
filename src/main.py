from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import atexit
from src.router.myrouter import router
from src.tasker.mytask import cleanup_unused_cache, top_in_cache



app = FastAPI()
app.include_router(router)

scheduler = BackgroundScheduler()

scheduler.add_job(
    func=cleanup_unused_cache,
    trigger=CronTrigger(hour=3, minute=0),
    id="cleanup_cache",
    name="Ежедневная очистка кэша",
    replace_existing=True
)
scheduler.add_job(
    func=top_in_cache,
    trigger=IntervalTrigger(minutes=10),
    id="update_top_links",
    name="Обновление топа ссылок",
    replace_existing=True
)

scheduler.start()
atexit.register(lambda: scheduler.shutdown())



@app.get("/")
def root():
    return {"message": "API для генерации коротких кодов", "docs": "/docs"}