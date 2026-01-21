# from django.core.management.base import BaseCommand
# from django.core.mail import EmailMessage
# from employee.models import Employee, EmployeeTimesheet
# from user_management.models import UserProfile
# from datetime import date, timedelta

# class Command(BaseCommand):
#     help = 'Send missed timesheet summary emails to employees'

#     def handle(self, *args, **options):
#         today = date.today()
#         employees = Employee.objects.filter(status='active')

#         for emp in employees:
#             user_profile = UserProfile.objects.filter(user_id=emp.employee_code).first()
#             if not user_profile or not user_profile.email:
#                 self.stdout.write(f"No email found for employee {emp.name} ({emp.employee_code}) - skipping")
#                 continue

#             joining_date = emp.joining_date
#             if not joining_date or joining_date > today:
#                 self.stdout.write(f"Invalid joining date for {emp.name} ({emp.employee_code}) - skipping")
#                 continue

#             # Generate date list from joining to today
#             total_days = (today - joining_date).days + 1
#             date_list = [joining_date + timedelta(days=i) for i in range(total_days)]

#             # All project codes the employee has worked on
#             project_codes = EmployeeTimesheet.objects.filter(
#                 employee_code=emp.employee_code
#             ).values_list('project_code__project_code', flat=True).distinct()

#             missed_entries = []

#             for dt in date_list:
#                 timesheets = EmployeeTimesheet.objects.filter(
#                     employee_code=emp.employee_code,
#                     date=dt
#                 )
#                 total_worked_seconds = sum([(ts.worked_hours or timedelta()).total_seconds() for ts in timesheets])
#                 total_worked_hours = round(total_worked_seconds / 3600, 2)

#                 if total_worked_hours < 8:
#                     missed_entries.append((dt, total_worked_hours))

#             if missed_entries:
#                 message = f"Dear {emp.name},<br><br>"
#                 message += f"The following dates have incomplete timesheet entries (less than 8 working hours logged):<br><br>"

#                 message += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
#                 message += "<tr><th>Date</th><th>Logged Hours</th><th>Your Projects</th></tr>"

#                 for missed_date, hours in missed_entries:
#                     project_list = ', '.join(project_codes) if project_codes else 'N/A'
#                     message += f"<tr><td>{missed_date.strftime('%Y-%m-%d')}</td><td>{hours:.2f}</td><td>{project_list}</td></tr>"

#                 message += "</table><br>"
#                 message += "Please log the remaining hours for the above dates in any of your assigned projects.<br><br>"
#                 message += "This is a system-generated reminder. Please contact your <b>Project Manager</b> if needed.<br><br>"
#                 message += "Regards,<br><b>PMO ROBOXA.</b>"

#                 email = EmailMessage(
#                     subject="Incomplete Timesheet Summary",
#                     body=message,
#                     to=[user_profile.email],
#                 )
#                 email.content_subtype = "html"
#                 email.send()

#                 self.stdout.write(f"Sent timesheet summary email to {emp.name}")
# from django.core.management.base import BaseCommand
# from django.core.mail import EmailMessage
# from employee.models import Employee, EmployeeTimesheet
# from user_management.models import UserProfile
# from datetime import date, timedelta, datetime

# class Command(BaseCommand):
#     help = 'Send missed timesheet summary emails to employees'

#     def handle(self, *args, **options):
#         today = date.today()
#         april_first = date(today.year, 4, 1)

#         # Find last Friday date
#         def get_last_friday(ref_date):
#             days_since_friday = (ref_date.weekday() - 4) % 7  # Friday is weekday 4
#             last_friday = ref_date - timedelta(days=days_since_friday)
#             return last_friday

#         last_friday = get_last_friday(today)

#         employees = Employee.objects.filter(status='active')

#         for emp in employees:
#             user_profile = UserProfile.objects.filter(user_id=emp.employee_code).first()
#             if not user_profile or not user_profile.email:
#                 self.stdout.write(f"No email found for employee {emp.name} ({emp.employee_code}) - skipping")
#                 continue

#             # Use April 1st as start date (ignore joining or project start date for now)
#             start_date = april_first
#             end_date = last_friday

#             if start_date > end_date:
#                 self.stdout.write(f"Skipping {emp.name} since start_date {start_date} is after end_date {end_date}")
#                 continue

#             total_days = (end_date - start_date).days + 1
#             date_list = [start_date + timedelta(days=i) for i in range(total_days)]

#             # Get distinct project codes the employee has worked on overall (not filtered by date)
#             project_codes = EmployeeTimesheet.objects.filter(
#                 employee_code=emp.employee_code
#             ).values_list('project_code__project_code', flat=True).distinct()

#             missed_entries = []

#             for dt in date_list:
#                 timesheets = EmployeeTimesheet.objects.filter(
#                     employee_code=emp.employee_code,
#                     date=dt
#                 )
#                 total_worked_seconds = sum([(ts.worked_hours or timedelta()).total_seconds() for ts in timesheets])
#                 total_worked_hours = round(total_worked_seconds / 3600, 2)

#                 if total_worked_hours < 8:
#                     missed_entries.append((dt, total_worked_hours))

#             if missed_entries:
#                 message = f"Dear {emp.name},<br><br>"
#                 message += f"Please find below mentioned dates (with 0 to < 8 working hours), pending for your time sheet entry:<br><br>"

#                 message += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
#                 message += "<tr><th>Missed Dates</th><th>Logged Hours</th><th>Projects</th></tr>"

#                 for missed_date, hours in missed_entries:
#                     project_list = ', '.join(project_codes) if project_codes else 'N/A'
#                     message += f"<tr><td>{missed_date.strftime('%Y-%m-%d')}</td><td>{hours:.2f}</td><td>{project_list}</td></tr>"

#                 message += "</table><br>"
#                 message += "Please log your entries for the above dates, under the projects assigned to you.<br><br>"
#                 message += "This is a system-generated reminder. Please contact your <b>Project Manager</b> further calrification if any.<br><br>"
#                 message += "Regards,<br><b>PMO ROBOXA.</b>"

#                 email = EmailMessage(
#                     subject="Incomplete Timesheet Summary",
#                     body=message,
#                     to=[user_profile.email],
#                 )
#                 email.content_subtype = "html"
#                 email.send()

#                 self.stdout.write(f"Sent timesheet summary email to {emp.name}")
#             else:
#                 self.stdout.write(f"No incomplete timesheets for {emp.name}")

from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from employee.models import Employee, EmployeeTimesheet
from user_management.models import UserProfile
from datetime import date, timedelta
from pmo.models import Project

class Command(BaseCommand):
    help = 'Send missed timesheet summary emails to employees'

    def calculate_working_days(self, start_date, end_date):
        working_days = []
        current = start_date
        while current <= end_date:
            # Exclude Saturday (5) and Sunday (6)
            if current.weekday() < 5:
                working_days.append(current)
            current += timedelta(days=1)
        return working_days

    def handle(self, *args, **options):
        today = date.today()
        april_first = date(today.year, 4, 1)

        def get_last_friday(ref_date):
            days_since_friday = (ref_date.weekday() - 4) % 7  # Friday = 4
            last_friday = ref_date - timedelta(days=days_since_friday)
            return last_friday

        last_friday = get_last_friday(today)

        employees = Employee.objects.filter(status='active')

        for emp in employees:
            # Skip specific employee
            if emp.name.strip() == "Sudhakara Varma Yarramraju":
                self.stdout.write(f"Skipping email for {emp.name}")
                continue

            user_profile = UserProfile.objects.filter(user_id=emp.employee_code).first()
            if not user_profile or not user_profile.email:
                self.stdout.write(f"No email found for employee {emp.name} ({emp.employee_code}) - skipping")
                continue

            # start_date = april_first
            start_date = max(april_first, emp.joining_date)

            end_date = last_friday

            if start_date > end_date:
                self.stdout.write(f"Skipping {emp.name} since start_date {start_date} is after end_date {end_date}")
                continue

            working_days = self.calculate_working_days(start_date, end_date)

            project_codes = EmployeeTimesheet.objects.filter(
                employee_code=emp.employee_code
            ).values_list('project_code__project_code', flat=True).distinct()

            missed_entries = []

            for dt in working_days:
                timesheets = EmployeeTimesheet.objects.filter(
                    employee_code=emp.employee_code,
                    date=dt
                )
                total_worked_seconds = 0
                for ts in timesheets:
                    wh = ts.worked_hours
                    if isinstance(wh, timedelta):
                        total_worked_seconds += wh.total_seconds()
                    elif isinstance(wh, (int, float)):
                        total_worked_seconds += wh * 3600
                    else:
                        total_worked_seconds += 0

                total_worked_hours = round(total_worked_seconds / 3600, 2)

                if total_worked_hours < 8:
                    missed_entries.append((dt, total_worked_hours))
                    

            if missed_entries:
                message = f"Dear {emp.name},<br><br>"
                # message += ("Please find below mentioned dates (with 0 to < 8 working hours), pending for your time sheet entry:<br><br>")
                # Collect all project descriptions
                project_objs = Project.objects.filter(project_code__in=project_codes)
                project_descriptions = set(proj.project_description for proj in project_objs)

                # Add the default project if applicable
                default_project = Project.objects.filter(project_description='Internal Project').first()
                if default_project:
                    project_descriptions.add(default_project.project_description)

                project_description_text = ', '.join(sorted(project_descriptions))

                message += (
                    f"Please find below mentioned dates (with 0 to < 8 working hours), "
                    f"pending for your time sheet entry under the following project: "
                    f"<b>{project_description_text}</b><br><br>"
                )

                message += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
                message += "<tr><th>Missed Dates</th><th>Logged Hours</th><th>Projects</th></tr>"

                for missed_date, hours in missed_entries:
                    # project_list = ', '.join(project_codes) if project_codes else 'N/A'
                    project_code_set = set(project_codes)

                    # Add the default internal project by description
                    default_project = Project.objects.filter(project_description='Internal Project').first()
                    if default_project:
                        project_code_set.add(default_project.project_code)

                    project_list = ', '.join(sorted(project_code_set))


                    message += f"<tr><td>{missed_date.strftime('%Y-%m-%d')}</td><td>{hours:.2f}</td><td>{project_list}</td></tr>"

                message += "</table><br>"
                message += ("Please log your entries for the above dates, under the projects assigned to you.<br><br>")

                #  Add new detailed note here
                message += (
                    "<p><strong>For Your Information:</strong><br>"
                    "Please check the network you are connected to and use the appropriate URL below to access the <strong>PMO Application:</strong><br>"
                    "If you are connected to the <strong>'Roboxa' network,</strong> please use: <a href='http://pmo.roboxaservices.com/'>http://pmo.roboxaservices.com/</a><br>"
                    "If you are connected otherthan <strong>'Roboxa' network (VPN or external network),</strong> please use: <a href='http://pub-pmo.roboxaservices.com/'>http://pub-pmo.roboxaservices.com/</a></p>"
                )

                message += ("This is a system-generated reminder. Please contact your <b>Project Manager</b> for further clarifications if any.<br><br>")
                message += "Regards,<br><b>PMO ROBOXA.</b>"


                email = EmailMessage(
                    subject="Incomplete Timesheet Summary",
                    body=message,
                    to=[user_profile.email],
                )
                email.content_subtype = "html"
                email.send()

                self.stdout.write(f"Sent timesheet summary email to {emp.name}")
            else:
                self.stdout.write(f"No incomplete timesheets for {emp.name}")



