# from django_cron import CronJobBase, Schedule
# from .views import get_missed_timesheet_dates  # Assuming the view is within views.py

# class SendMissedTimesheetEmailJob(CronJobBase):
#     schedule = Schedule(run_every_mins=1440)  # The task runs daily
#     code = 'employee.send_missed_timesheet_email_job'  # Unique code for the cron job

#     def do(self):
#         from django.utils.timezone import now
#         from datetime import timedelta

#         current_time = now()

#         # Check if today is friday and time is 3:05 PM
#         if current_time.weekday() == 4 and current_time.hour == 9 :  #
#             # Run the logic to send the email for missed timesheet dates
#             employee_code = "RBX9999"  # You can adjust how employee_code is retrieved

#             # Simulating the function, ideally this would be fetching employee_code dynamically
#             request_data = {"employee_code": employee_code}  # You can simulate request data as needed
#             class DummyRequest:
#                 def __init__(self, data):
#                     self.data = data

#             request = DummyRequest(request_data)
#             get_missed_timesheet_dates(request)

# # all employees
# # from django_cron import CronJobBase, Schedule
# # from .views import get_missed_timesheet_dates
# # from employee.models import Employee  # Import your Employee model

# # class SendMissedTimesheetEmailJob(CronJobBase):
# #     schedule = Schedule(run_every_mins=1440)  # Run daily
# #     code = 'employee.send_missed_timesheet_email_job'  # Unique code for the cron job

# #     def do(self):
# #         from django.utils.timezone import now
# #         from datetime import timedelta

# #         current_time = now()

# #         # Run only on Friday at 9:00 AM
# #         if current_time.weekday() == 4 and current_time.hour == 9:
# #             employees = Employee.objects.all()  # Optionally filter for active employees

# #             class DummyRequest:
# #                 def __init__(self, data):
# #                     self.data = data

# #             for employee in employees:
# #                 employee_code = employee.employee_code
# #                 request_data = {"employee_code": employee_code}
# #                 request = DummyRequest(request_data)

# #                 try:
# #                     # This view both processes data and sends email
# #                     get_missed_timesheet_dates(request)
# #                 except Exception as e:
# #                     print(f"Failed to send email for {employee_code}: {str(e)}")
