from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from employee.models import Employee, EmployeeTimesheet
from user_management.models import UserProfile
from pmo.models import ProjectTeam
from datetime import date, timedelta
from collections import defaultdict


class Command(BaseCommand):
    help = 'Send consolidated missed timesheet summaries to management'

    def handle(self, *args, **options):
        today = date.today()
        april_first = date(today.year, 4, 1)

        def get_last_friday(ref_date):
            days_since_friday = (ref_date.weekday() - 4) % 7
            return ref_date - timedelta(days=days_since_friday)

        last_friday = get_last_friday(today)
        start_date = april_first
        end_date = last_friday

        if start_date > end_date:
            self.stdout.write("Start date is after end date. Exiting.")
            return

        total_days = (end_date - start_date).days + 1
        date_list = [
            start_date + timedelta(days=i)
            for i in range(total_days)
            if (start_date + timedelta(days=i)).weekday() < 5  # Only weekdays
        ]

        # management_name -> { 'email': email, 'projects': { project_name: { employee_name: missed_count } } }
        mgmt_data = {}

        employees = Employee.objects.filter(status='active')

        for emp in employees:
            timesheet_data = {dt: 0.0 for dt in date_list}

            emp_timesheets = EmployeeTimesheet.objects.filter(
                employee_code=emp.employee_code,
                date__range=(start_date, end_date)
            )

            for ts in emp_timesheets:
                if ts.date in timesheet_data:
                    seconds = (ts.worked_hours or timedelta()).total_seconds()
                    timesheet_data[ts.date] += round(seconds / 3600, 2)

            missed_dates = [(dt, hrs) for dt, hrs in timesheet_data.items() if hrs < 8]

            if missed_dates:
                project_teams = ProjectTeam.objects.filter(employee_code=emp)
                for pt in project_teams:
                    project = pt.project_code

                    # Skip internal/default projects
                    if project.project_description.strip().lower() in ['internal project', 'default project']:
                        continue

                    management_name = project.management

                    if not management_name:
                        continue

                    # Fetch management user profile
                    management_user = UserProfile.objects.filter(name__iexact=management_name).first()
                    if not management_user or not management_user.email:
                        self.stdout.write(
                            f"No email found for Management: {management_name} (employee: {emp.name})"
                        )
                        continue

                    if management_name not in mgmt_data:
                        mgmt_data[management_name] = {
                            'email': management_user.email,
                            'projects': defaultdict(dict)
                        }

                    missed_count = len(missed_dates)
                    mgmt_data[management_name]['projects'][project.project_description][emp.name] = missed_count

        # Send summary emails
        for management_name, data in mgmt_data.items():
            email = data['email']
            projects = data['projects']

            message = f"Dear {management_name},<br><br>"
            message += "Here is the summary of employees with incomplete timesheet entries (less than 8 hours) across your projects:<br><br>"

            for project_name, emp_data in projects.items():
                message += f"<b>Project: {project_name}</b><br>"
                message += (
                    "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
                )
                message += "<tr><th>Employee Name</th><th>Missed Dates Count</th></tr>"
                for emp_name, missed_count in emp_data.items():
                    message += f"<tr><td>{emp_name}</td><td>{missed_count}</td></tr>"
                message += "</table><br>"

            message += "This is a system-generated reminder.<br><br>"
            message += "Regards,<br><b>PMO ROBOXA.</b>"

            email_msg = EmailMessage(
                subject="Timesheet Reminder: Incomplete Entries",
                body=message,
                to=[email]
            )
            email_msg.content_subtype = "html"
            email_msg.send()

            self.stdout.write(f"Consolidated email sent to Management: {management_name}")