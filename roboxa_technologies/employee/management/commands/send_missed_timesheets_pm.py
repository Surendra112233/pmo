from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from employee.models import Employee, EmployeeTimesheet
from user_management.models import UserProfile
from pmo.models import ProjectTeam, ProjectTeamAllocation
from datetime import date, timedelta
from collections import defaultdict


class Command(BaseCommand):
    help = 'Send missed timesheet summaries to Project Managers'

    def parse_hours(self, value):
        if not value:
            return 0.0

        value = str(value).strip()

        if value.isdigit() or value.replace('.', '', 1).isdigit():
            return round(float(value), 2)

        parts = value.split(':')
        try:
            if len(parts) == 2:  
                h, m = int(parts[0]), int(parts[1])
                return round(h + m/60, 2)

            if len(parts) == 3:  
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                return round(h + m/60 + s/3600, 2)

        except:
            return 0.0

        return 0.0

    def handle(self, *args, **options):

        today = date.today()
        april_first = date(today.year, 4, 1)

        def get_last_friday(ref_date):
            days_since_friday = (ref_date.weekday() - 4) % 7
            return ref_date - timedelta(days=days_since_friday)

        start_date = april_first
        end_date = today

        if start_date > end_date:
            self.stdout.write("Start date is after end date. Exiting.")
            return

        # Weekdays only
        base_date_list = [
            start_date + timedelta(days=i)
            for i in range((end_date - start_date).days + 1)
            if (start_date + timedelta(days=i)).weekday() < 5
        ]

        pm_missed_data = defaultdict(lambda: defaultdict(list))
        pm_emails = {}

        # ---- NEW: FETCH ONLY PMO ROLE EMAILS ---- #
        PMO_EMAILS = set(
            UserProfile.objects.filter(role__iexact="PMO")
            .exclude(email__isnull=True)
            .values_list("email", flat=True)
        )

        employees = Employee.objects.filter(status='active')

        for emp in employees:

            project_teams = ProjectTeam.objects.filter(employee_code=emp)

            for pt in project_teams:
                project = pt.project_code

                if not project:
                    continue

                # Skip internal/default projects
                if project.project_description.strip().lower() in ["internal project", "default project"]:
                    continue

                pm_name = project.project_manager
                if not pm_name:
                    continue

                pm_user = UserProfile.objects.filter(name__iexact=pm_name).first()
                if pm_user and pm_user.email:
                    pm_emails[pm_name] = pm_user.email
                else:
                    self.stdout.write(f"No email found for PM: {pm_name} (employee: {emp.name})")
                    continue

                allocation_start = pt.start_date
                allocation_end = pt.end_date

                project_date_list = [
                    d for d in base_date_list
                    if allocation_start <= d <= allocation_end
                ]

                if not project_date_list:
                    continue

                pta = ProjectTeamAllocation.objects.filter(
                    employee_code=emp, project_code=project
                ).first()

                if pta:
                    allocation_percent = pta.allocation_percent
                else:
                    allocation_percent = 100  # fallback

                expected_hours = round((allocation_percent / 100) * 8, 2)

                project_timesheet_data = {dt: 0.0 for dt in project_date_list}

                emp_timesheets = EmployeeTimesheet.objects.filter(
                    employee_code=emp,
                    project_code=project,
                    date__range=(allocation_start, allocation_end)
                )

                for ts in emp_timesheets:
                    if ts.date not in project_timesheet_data:
                        continue

                    logged_hours = self.parse_hours(ts.worked_hours)
                    project_timesheet_data[ts.date] += logged_hours

                missed_dates = []
                for dt, logged in project_timesheet_data.items():

                    if round(logged, 2) >= round(expected_hours, 2):
                        continue

                    internal_ts = EmployeeTimesheet.objects.filter(
                        employee_code=emp,
                        date=dt,
                        project_code__project_description__iexact="Internal Project"
                    ).first()

                    if internal_ts:
                        internal_hours = self.parse_hours(internal_ts.worked_hours)
                        if round(internal_hours, 2) >= 8.0:
                            continue

                    missed_dates.append((dt, logged))

                if missed_dates:
                    key = (pm_name, project.project_description)
                    existing = set(pm_missed_data[key][emp.name])

                    for dt, hrs in missed_dates:
                        if (dt, hrs) not in existing:
                            pm_missed_data[key][emp.name].append((dt, hrs, allocation_percent))
                            existing.add((dt, hrs))

        # ----- SEND EMAILS — ONLY TO PMO ROLE USERS ----- #
        for (pm_name, project_name), emp_data in pm_missed_data.items():

            if pm_name not in pm_emails:
                self.stdout.write(f"Skipping email to {pm_name} — no email found.")
                continue

            # Check PMO-only condition
            if pm_emails[pm_name] not in PMO_EMAILS:
                self.stdout.write(f"Skipping email to {pm_name} — not a PMO role user.")
                continue

            message = f"Dear {pm_name},<br><br>"
            message += f"The following employees under your project <b>{project_name}</b> have incomplete timesheet entries:<br><br>"

            for emp_name, entries in emp_data.items():
                message += f"<b>{emp_name} (Allocation Percentage - {entries[0][2]}%)</b><br>"
                message += "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
                message += "<tr><th>Date</th><th>Logged Hours</th></tr>"
                for dt, hrs, alloc in sorted(entries):
                    message += f"<tr><td>{dt.strftime('%Y-%m-%d')}</td><td>{hrs:.2f}</td></tr>"
                message += "</table><br>"

            message += "<br>This is a system-generated reminder.<br><br>"
            message += "Regards,<br><b>PMO ROBOXA</b>"

            email = EmailMessage(
                subject=f"Timesheet Reminder: Incomplete Entries for Project {project_name}",
                body=message,
                to=[pm_emails[pm_name]]
            )
            email.content_subtype = "html"
            email.send()

            self.stdout.write(f"Email sent to PM {pm_name} for project '{project_name}'")
