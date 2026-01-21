from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import datetime, timedelta, date
from employee.models import EmployeeTimesheet
from pmo.models import ProjectTeam, Project
from master_data.models import Employee
from collections import defaultdict

class Command(BaseCommand):
    help = 'Send missed timesheet email notifications to employees'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        current_year = today.year
        friday = today - timedelta(days=today.weekday() - 4)  # Get this week's Friday
        friday_8am = datetime.combine(friday, datetime.min.time()) + timedelta(hours=8)

        employees = Employee.objects.all()

        for employee in employees:
            employee_projects = ProjectTeam.objects.filter(employee_code=employee)

            missed_dates = []

            for project_team in employee_projects:
                project = project_team.project_code
                project_start_date = project.start_date

                start_date = max(project_start_date, date(current_year, 4, 1))
                end_date = friday

                expected_dates = [
                    start_date + timedelta(days=x)
                    for x in range((end_date - start_date).days + 1)
                    if (start_date + timedelta(days=x)).weekday() < 5  # only weekdays
                ]

                submitted_dates = EmployeeTimesheet.objects.filter(
                    employee_code=employee,
                    project_code=project,
                    date__range=(start_date, end_date)
                ).values_list('date', flat=True)

                missed = [d for d in expected_dates if d not in submitted_dates]
                if missed:
                    missed_dates.extend(missed)

            if missed_dates:
                # Construct email
                subject = "Timesheet Reminder: Missed Dates Notification"
                missed_str = "\n".join([d.strftime('%d-%b-%Y') for d in sorted(missed_dates)])
                message = (
                    f"Dear {employee.name},\n\n"
                    f"You have not submitted timesheets for the following dates:\n\n"
                    f"{missed_str}\n\n"
                    "Please make sure to complete your timesheet entries at the earliest.\n\n"
                    "Regards,\nTimesheet Management System"
                )

                send_mail(
                    subject,
                    message,
                    'pmo-admin@roboxaservices.com',
                    [employee.official_email],  # use official email field
                    fail_silently=False,
                )

        self.stdout.write(self.style.SUCCESS("Missed timesheet notification emails sent."))
