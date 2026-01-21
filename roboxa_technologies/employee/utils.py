# from datetime import timedelta
# from django.utils import timezone
# from django.core.mail import EmailMessage
# from django.conf import settings
# from django.utils.html import escape

# from pmo.models import ProjectTeam
# from employee.models import EmployeeTimesheet,Employee
# from user_management.models import UserProfile

# #for all employyes
# # def send_missed_timesheet_email_to_all():
# #     employees = Employee.objects.all()  # You can add filters like active status if needed

# #     for emp in employees:
# #         employee_code = emp.employee_code
# #         result = send_missed_timesheet_email(employee_code)
# #         print(f"{employee_code} → {result}")


# def send_missed_timesheet_email(employee_code):
#     employee = Employee.objects.filter(employee_code=employee_code).first()
#     if not employee:
#         return f"Employee {employee_code} not found"
    

#     # Get all projects assigned to employee
#     employee_projects = ProjectTeam.objects.filter(employee_code=employee_code).select_related("project_code")

#     if not employee_projects.exists():
#         return f"No project allocations found for employee {employee_code}"

#     response_list = []

#     for emp_proj in employee_projects:
#         project = emp_proj.project_code
#         allocated_from = emp_proj.start_date
#         allocated_to = emp_proj.end_date or timezone.now().date()
#         allocated_to = min(allocated_to, timezone.now().date())

#         worked_dates = set(
#             EmployeeTimesheet.objects.filter(
#                 employee_code=employee_code,
#                 project_code=project,
#                 status="approved"
#             ).values_list("date", flat=True)
#         )

#         all_dates = [
#             (allocated_from + timedelta(days=i))
#             for i in range((allocated_to - allocated_from).days + 1)
#             if (allocated_from + timedelta(days=i)).weekday() < 5
#             and (allocated_from + timedelta(days=i)) <= timezone.now().date()
#         ]

#         missed_dates_with_hours = []

#         for date in all_dates:
#             worked_hours = 0
#             if date in worked_dates:
#                 worked_entry = EmployeeTimesheet.objects.filter(
#                     employee_code=employee_code,
#                     project_code=project,
#                     status="approved",
#                     date=date
#                 ).first()

#                 if worked_entry and worked_entry.worked_hours:
#                     if isinstance(worked_entry.worked_hours, timedelta):
#                         worked_hours = round(worked_entry.worked_hours.total_seconds() / 3600.0, 2)
#                     else:
#                         worked_hours = float(worked_entry.worked_hours)

#             expected_hours = 8
#             missed_hours = expected_hours - worked_hours

#             missed_dates_with_hours.append({
#                 "missed_date": str(date),
#                 "worked_hours": worked_hours,
#                 "missed_hours": missed_hours
#             })

#         response_list.append({
#             "project_code": project.project_code,
#             "project_name": project.project_description,
#             "missed_dates": missed_dates_with_hours
#         })

#     user_profile = UserProfile.objects.filter(user_id=employee_code).first()

#     if user_profile and user_profile.email and response_list:
#         subject = "Missed Timesheet Summary"

#         message_body = f"""
#         <p>Hi {escape(employee.name)},</p>

#         <p>Here is the summary of your missed timesheet entries:</p>

#         <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;">
#         <thead style="background-color: #f2f2f2; font-weight: bold;">
#             <tr>
#                 <th>Project Code</th>
#                 <th>Project Name</th>
#                 <th>Missed Date</th>
#                 <th>Logged Hours</th>
#             </tr>
#         </thead>
#         <tbody>
#         """

#         sorted_response_list = sorted(response_list, key=lambda x: (x['project_code'], x['project_name']))

#         for project_data in sorted_response_list:
#             project_code = project_data['project_code']
#             project_name = escape(project_data['project_name'])
#             missed_dates = sorted(project_data['missed_dates'], key=lambda x: x['missed_date'])

#             for date_info in missed_dates:
#                 missed_date = date_info['missed_date']
#                 logged_hours = round(date_info['worked_hours'], 2)

#                 message_body += f"""
#                     <tr>
#                         <td>{project_code}</td>
#                         <td>{project_name}</td>
#                         <td>{missed_date}</td>
#                         <td style="text-align:right">{logged_hours}</td>
#                     </tr>
#                 """

#         message_body += """
#         </tbody>
#         </table>

#         <p>Please ensure to fill the missing entries at the earliest.</p>

#         <p>Best regards,<br>PMO ROBOXA</p>
#         """

#         try:
#             email = EmailMessage(
#                 subject=subject,
#                 body=message_body,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[user_profile.email]
#             )
#             email.content_subtype = "html"
#             email.send()
#             return f"Email sent to {user_profile.email}"
#         except Exception as e:
#             return f"Failed to send email: {str(e)}"

#     return "No email sent — user email missing or no missed data"

