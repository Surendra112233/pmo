from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from datetime import date, timedelta
from openpyxl import Workbook
from io import BytesIO
from pmo.models import Project, ProjectTeam, ProjectTeamAllocationHistory
from user_management.models import UserRoleAssign


class Command(BaseCommand):
    help = "Send Employee Project Duration Report with Excel attachment"

    def handle(self, *args, **kwargs):
        today = date.today()
        cutoff_date = today + timedelta(days=90)

        delivery_head_users = UserRoleAssign.objects.filter(
            role_name__contains=["DeliveryHead"],    
            status__iexact="active"
        )
        delivery_head_emails = list(delivery_head_users.values_list("email", flat=True))

        static_emails = [
            "varma@roboxaservices.com",
            "nageswara.k@roboxaservices.com",
        ]

        recipients = list(set(delivery_head_emails + static_emails))

        if not recipients:
            self.stdout.write(self.style.WARNING("No recipients found for DeliveryHead role"))

        html_content = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #000;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 10px;
                margin-bottom: 30px;
            }}
            th, td {{
                border: 1px solid #000;
                padding: 6px;
                text-align: left;
            }}
        </style>
        </head>
        <body>
        <p>Hi All,</p>
        <p>
            Here is the summary of employees scheduled to be relieved from their respective projects 
            within the next 90 days from today.
        </p>
        """

        projects = Project.objects.filter(project_status__in=["active", "open"])

        employees_qs = (
            ProjectTeam.objects.filter(
                project_code__in=projects,
                end_date__gte=today,
                end_date__lte=cutoff_date,
                employee_code__status__iexact="active",
            )
            .select_related("employee_code", "project_role", "task", "project_code")
            .order_by("end_date")
        )

        # Prepare Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Employee Project Duration"

        headers = [
            "Project Name",
            "Employee No",
            "Employee Name",
            "Project Specific",
            "Contractor",
            "Primary Skills",
            "Secondary Skills",
            "End Date",
            "Allocation % (on End Date)",
        ]
        ws.append(headers)

        if not employees_qs.exists():
            html_content += "<p><b>No active/open employees found with end dates within 90 days.</b></p>"
        else:
            html_content += """
            <table>
                <tr>
                    <th>Project Name</th>
                    <th>Employee Code</th>
                    <th>Employee Name</th>
                    <th>Project Specific Hire</th>
                    <th>Contractor</th>
                    <th>Primary Skills</th>
                    <th>Secondary Skills</th>
                    <th>End Date</th>
                    <th>Allocation % (as on End Date)</th>
                </tr>
            """

            for emp in employees_qs:
                emp_obj = emp.employee_code
                project = emp.project_code
                end_date = emp.end_date

                # Allocation % on end date
                allocation_history = (
                    ProjectTeamAllocationHistory.objects.filter(
                        allocation__employee_code=emp_obj,
                        allocation__project_code=project,
                        allocation_start_date__lte=end_date,
                        allocation_end_date__gte=end_date,
                    )
                    .order_by("-updated_at")
                    .first()
                )
                allocation_percent = allocation_history.allocation_percent if allocation_history else 0

                project_specific = (
                    "Yes"
                    if getattr(emp_obj, "project_specific_hire", "")
                    and str(emp_obj.project_specific_hire).strip().lower() in ("yes", "y", "true", "1")
                    else "No"
                )

                contractor = "Yes" if getattr(emp_obj, "contractor", None) else "No"

                def format_skill(skill_list):
                    if not skill_list:
                        return "-"
                    if isinstance(skill_list, list):
                        cleaned = [str(s).strip() for s in skill_list if str(s).strip()]
                        return ", ".join(cleaned) if cleaned else "-"
                    return str(skill_list) or "-"

                primary_skill = format_skill(getattr(emp_obj, "primary_skill", []))
                secondary_skill = format_skill(getattr(emp_obj, "secondary_skill", []))

                html_content += f"""
                <tr>
                    <td>{project.project_description} ({project.project_code})</td>
                    <td>{emp_obj.employee_code}</td>
                    <td>{emp_obj.name}</td>
                    <td>{project_specific}</td>
                    <td>{contractor}</td>
                    <td>{primary_skill}</td>
                    <td>{secondary_skill}</td>
                    <td>{end_date.strftime('%d-%b-%Y')}</td>
                    <td>{allocation_percent}%</td>
                </tr>
                """

                ws.append([
                    f"{project.project_description} ({project.project_code})",
                    emp_obj.employee_code,
                    emp_obj.name,
                    project_specific,
                    contractor,
                    primary_skill,
                    secondary_skill,
                    end_date.strftime("%d-%b-%Y"),
                    f"{allocation_percent}%",
                ])

            html_content += "</table>"

        html_content += """
        <p>This is a system-generated reminder.</p>
        <p>Regards,<br><b>PMO ROBOXA</b></p>
        </body></html>
        """

        # Save workbook once
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        excel_data = excel_buffer.getvalue()

        # Send individually to each recipient
        for recipient in recipients:
            email = EmailMessage(
                subject="Employee Project Duration Report",
                body=html_content,
                from_email="pmo-admin@roboxaservices.com",
                to=[recipient],
            )
            email.content_subtype = "html"
            email.attach(
                "Employee_Project_Duration_Report.xlsx",
                excel_data,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            try:
                email.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f"Email sent successfully to {recipient}!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email to {recipient}: {e}"))