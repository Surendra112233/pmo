from django.urls import path
from .views import get_timesheet_for_approval,get_timesheet_for_approval_all,approve_or_reject_timesheet,get_project_summary,get_project_detailed_summary,get_employee_summary,get_employee_detailed_summary,get_project_hours_by_project,get_project_summary_periodwise,get_project_detailed_periodwise
urlpatterns = [
    path('timesheet/approve/', get_timesheet_for_approval, name='approve_timesheet'),
    path('timesheet/approve/all/', get_timesheet_for_approval_all, name='approve_timesheet_all'),
    path('timesheet/approve/reject/', approve_or_reject_timesheet, name='approve_or_reject'),
    path('project-summary/',get_project_summary, name='display_prject_summary'),
    path('project-detailed/', get_project_detailed_summary, name='display_project_detailed_bytask'),
    path('employee-summary/', get_employee_summary, name='display_employee_summary'),
    path('employee-detailed/', get_employee_detailed_summary, name="display_employee_deatiled_bytask"),
    path('get-projecthours-by-proejct/',get_project_hours_by_project, name='display_projecthours'),
    path("get_project_summary_periodwise/",get_project_summary_periodwise,name="get_project_summary_periodwise"),
    path("get_project_detailed_periodwise/",get_project_detailed_periodwise,name="get_project_detailed_periodwise"),
    # path("get_missed_timesheet_summary/",get_missed_timesheet_summary,name="get_missed_timesheet_summary")


]