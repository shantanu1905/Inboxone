from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time

# Define the recurring task
def my_recurring_task():
    print(f"Task running at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Initialize the APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Schedule the recurring task
scheduler.add_job(
    my_recurring_task,
    trigger=IntervalTrigger(seconds=10),  # Execute every 10 seconds
    id='my_recurring_task',
    replace_existing=True
)