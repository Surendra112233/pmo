from django.core.management.base import BaseCommand
from employee.management.commands.scheduler import stop

class Command(BaseCommand):
    help = 'Stops the background APScheduler jobs'

    def handle(self, *args, **kwargs):
        self.stdout.write("Stopping scheduler...")
        stop()
        self.stdout.write("Scheduler stopped.")
