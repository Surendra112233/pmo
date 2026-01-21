import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from django.core.management import call_command
from django.core.management.base import BaseCommand
import os
from decouple import config

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None

# Job functions
def send_timesheet_emails():
    logger.info("send_timesheet_emails job triggered")
    try:
        call_command('send_missed_timesheets_emp')
        logger.info("Successfully sent missed timesheet summary emails.")
    except Exception as e:
        logger.error(f"Error running employee email command: {e}")

def send_timesheet_pm_emails():
    logger.info("send_timesheet_pm_emails job triggered")
    try:
        call_command('send_missed_timesheets_pm')
        logger.info("Successfully sent missed timesheet summary emails to PMs.")
    except Exception as e:
        logger.error(f"Error running PM email command: {e}")

def send_timesheet_dh_emails():
    logger.info("send_timesheet_dh_emails job triggered")
    try:
        call_command('send_missed_timesheets_dh')
        logger.info("Successfully sent missed timesheet summary emails to Delivery Heads.")
    except Exception as e:
        logger.error(f"Error running DH email command: {e}")

def send_timesheet_mgt_emails():
    logger.info("send_timesheet_mgt_emails job triggered")
    try:
        call_command('send_missed_timesheets_mgt')
        logger.info("Successfully sent missed timesheet summary emails to Management.")
    except Exception as e:
        logger.error(f"Error running Management email command: {e}")

def send_approvals_dh():
    logger.info("send_approvals_dh job triggered")
    try:
        call_command('send_pending_approvals_dh')
        logger.info("Successfully sent pending approvals emails to Delivery Heads.")
    except Exception as e:
        logger.error(f"Error sending pending approvals emails: {e}")

# Scheduler start function
def start():
    global scheduler

    db_name = config("DATABASE_NAME", default="").strip()
    if db_name == "pmo_rbx":
        logger.info("Scheduler not started because DATABASE_NAME is pmo_rbx.")
        return
    
    if scheduler and scheduler.running:
        logger.info("Scheduler already running, skipping start.")
        return

    scheduler = BackgroundScheduler(timezone=timezone("Asia/Kolkata"))

    scheduler.add_job(send_timesheet_emails, CronTrigger(day_of_week='fri', hour=9, minute=0), id='emp', replace_existing=True)
    scheduler.add_job(send_timesheet_pm_emails, CronTrigger(day_of_week='fri', hour=9, minute=0), id='pm', replace_existing=True)
    scheduler.add_job(send_timesheet_dh_emails, CronTrigger(day_of_week='mon', hour=9, minute=0), id='dh', replace_existing=True)
    scheduler.add_job(send_approvals_dh, CronTrigger(day_of_week='mon', hour=9, minute=0), id='approvals_mon', replace_existing=True)
    scheduler.add_job(send_approvals_dh, CronTrigger(day_of_week='wed', hour=9, minute=0), id='approvals_wed', replace_existing=True)
    scheduler.add_job(send_timesheet_mgt_emails, CronTrigger(day_of_week='wed', hour=9, minute=0), id='mgt', replace_existing=True)

    scheduler.start()
    logger.info("All scheduled jobs have been started.")

# Django management command class
class Command(BaseCommand):
    help = 'Start the APScheduler background jobs'

    def handle(self, *args, **kwargs):
        # Prevent scheduler running twice due to Django autoreload in development
        if os.environ.get('RUN_MAIN') == 'true':
            self.stdout.write("Starting scheduler...")
            start()


def stop():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully.")
    else:
        logger.info("Scheduler is not running.")