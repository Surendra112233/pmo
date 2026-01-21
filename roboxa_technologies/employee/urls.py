from django.urls import path
from . import views


urlpatterns = [
    path('timesheet-add/', views.add_timesheet, name='add_employee_timesheet'),
    path('timesheet-edit/', views.edit_timesheet, name='edit_employee_timesheet'),
    path('display-timesheet/', views.display_timesheets, name='display_employee_timesheets'),
    path('timesheets/employee_month_year/', views.display_timesheets_by_employee_code, name='display_timesheets_by_employee_month_year'),
    path('display-timesheet-byid/<int:pk>', views.get_timesheet_by_id, name='display_timesheet_byid'),
    path('display-timesheet/<str:employee_code>/',views.get_timesheets_by_employee_code, name='display_timesheet_employeecode'),
    path('delete-timesheet/<int:pk>/', views.delete_timesheet, name='delete_timesheet'),
    path('display-employee-projects/<str:employee_code>/', views.get_employee_projects, name='diplay_employee_projects'),
    path('get-project-hours/', views.get_project_hours_by_employee, name='display_project_hours'),
    path('emp-utilization-report/', views.emp_utilization_report, name='emp_utilization_report'),
    # path("api/timesheet/missed-dates/", views.get_missed_timesheet_dates, name="missed-timesheet-dates"),
    path('get_project_duration_report/', views.get_project_duration_report, name='get_project_duration_report'),
    path('get_countries_list/', views.get_countries_list, name='get_countries_list')



]
