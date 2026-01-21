from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from collections import defaultdict
from employee.models import EmployeeTimesheet
from user_management.models import UserProfile
from pmo.models import Project
from datetime import date


class Command(BaseCommand):
    help = 'Send notification to Delivery Heads for pending timesheet approvals'

    def handle(self, *args, **options):
        today = date.today()

        # ---- NEW: Fetch all DeliveryHead role emails ----
        DELIVERY_HEAD_EMAILS = set(
            UserProfile.objects.filter(
                userroleassign__role_name__contains=["DeliveryHead"]
            ).values_list("email", flat=True)
        )


        pending_timesheets = EmployeeTimesheet.objects.filter(status='open')

        # Structure: {delivery_head: {project_description: {employee_name: [dates]}}}
        dh_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        dh_emails = {}

        for ts in pending_timesheets:

            # --- Standardize project_identifier ---
            project_identifier = ts.project_code

            if isinstance(project_identifier, Project):
                project_identifier = project_identifier.project_code
            else:
                project_identifier = str(project_identifier).strip()

            project = Project.objects.filter(project_code=project_identifier).first()

            if not project:
                project = Project.objects.filter(project_description__iexact=project_identifier).first()

            if not project:
                self.stdout.write(f"Project not found for: {project_identifier}")
                continue

            employee_name = ts.employee_name
            timesheet_date = ts.date

            delivery_head_name = project.delivery_head
            if not delivery_head_name:
                self.stdout.write(f"No Delivery Head assigned for: {project.project_code}")
                continue

            # --- Get Delivery Head Email ---
            if delivery_head_name not in dh_emails:
                user_profile = UserProfile.objects.filter(name__iexact=delivery_head_name).first()
                if user_profile and user_profile.email:
                    dh_emails[delivery_head_name] = user_profile.email
                else:
                    self.stdout.write(f"No email found for Delivery Head: {delivery_head_name}")
                    continue

            # Group data
            dh_data[delivery_head_name][project.project_description][employee_name].append(timesheet_date)

        # ---- Send grouped emails ----
        for dh_name, projects in dh_data.items():

            dh_email = dh_emails.get(dh_name)

            # ---- NEW: Check based on DeliveryHead role ----
            if dh_email not in DELIVERY_HEAD_EMAILS:
                self.stdout.write(f"Skipping email for {dh_name} ({dh_email}) — Not a DeliveryHead role user")
                continue

            # Build message
            message = f"Dear {dh_name},<br><br>"
            message += "The following timesheet entries are pending your approval:<br><br>"

            message += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
            message += "<tr><th>Project</th><th>Employee Name</th><th>Pending Dates</th></tr>"

            for project_name, employees in projects.items():
                for emp_name, dates in employees.items():
                    dates_str = "<br>".join(dt.strftime('%Y-%m-%d') for dt in sorted(dates))
                    message += f"<tr><td>{project_name}</td><td>{emp_name}</td><td>{dates_str}</td></tr>"

            message += "</table><br>"
            message += "This is a system-generated reminder.<br><br>"
            message += "Regards,<br><b>PMO ROBOXA</b>"

            email = EmailMessage(
                subject=f"Timesheet Approvals - {today.strftime('%Y-%m-%d')}",
                body=message,
                to=[dh_email]
            )
            email.content_subtype = "html"
            email.send()

            self.stdout.write(f"Email sent to Delivery Head: {dh_name}")
