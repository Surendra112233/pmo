from django.urls import path
from . import views
# from pmo.views import PhaseAllocationDeleteView,GetAllPhaseAllocationsView,BulkPhaseAllocationUpdateView,GetPhaseAllocationsByProjectView,
from pmo.views import PhaseAllocationCreateView,PhaseAllocationBulkCreateView,PhaseAllocationListView,PhaseAllocationDeleteView,GetPhaseAllocationsByProjectView,PMOReportAPIView,get_employee_projects, get_project_employee_details,MissedTimesheetSummaryAPI,get_projects_by_type
from pmo.views import get_employee_allocation_timesheet

urlpatterns = [
    path('add-project/', views.add_project, name='add_project'),
    path('get-projects/', views.get_projects, name='get_projects'),
    path('get-project-by-code/<str:project_code>/', views.get_project_by_code, name='get_project_by_code'),
    # path('get-project-by-code/<str:project_code>/', views.get_project_by_code),
    path('edit-project/<str:project_code>/', views.edit_project, name='edit_project'),
    path('delete-project-by-code/<str:project_code>/', views.delete_project, name='delete_project'),
    path('add-project-team/', views.add_project_team, name='add_project_team'),
    path('edit-project-team/', views.edit_project_team, name='edit_project_team'),
    path('display-project-team', views.get_project_teams, name='display_project_team'),
    # path('update-project-team/<int:pk>/', views.update_project_team, name='update_project_team'),
    path('delete-project-team/<int:pk>/', views.delete_project_team, name='delete_project_team'),
    path('delete-project-team-bulk/', views.bulk_delete_project_teams, name='bulk-delete-project-teams'),
    path('phase-allocation-create/', PhaseAllocationCreateView.as_view(), name='phase-allocation'),
    path('phase-allocation-create-bulk',PhaseAllocationBulkCreateView.as_view(), name='create_bulk_phase_allocation'),
    path('phase-allocation/delete/<int:pk>/', PhaseAllocationDeleteView.as_view(), name='delete_phase_allocation'),
    path('phase-allocation/update-bulk/', views.bulk_update_phase_allocations, name='update_bulk_phase_allocation'),
    path('pmo/phase-allocation/all/', PhaseAllocationListView.as_view(), name='get_all_phase_allocations'),
    path('pmo/phase-allocation/by-project/', GetPhaseAllocationsByProjectView.as_view(), name='get_phase_allocations_by_project'),
    path('pmo-report/', PMOReportAPIView.as_view(), name='pmo-report'),
    path('pmo-missed_timesheet/', MissedTimesheetSummaryAPI.as_view(), name='pmo-missed_timesheet'),
    path('assign-allocation/', views.assign_allocation_percent, name = 'assign_allocation_percent'),
    path('employee-availability/', views.employee_availability_report, name = 'employee_availability_report'),
    # path('api/employee/<str:employee_code>/projects/', get_employee_projects, name='employee-projects'),
    path('api/project/<str:project_code>/employee-details/', views.get_project_employee_details, name='get_project_employee_details'),
    path('api/employee-allocation-timesheet/',views.get_employee_allocation_timesheet,name='get_employee_allocation_timesheet'),
    path('api/get_projects_by_type/',views.get_projects_by_type,name='get_projects_by_type'),
    path('api/employee/<str:employee_code>/projects/', get_employee_projects, name='employee-projects'),



]   


