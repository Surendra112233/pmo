from django.urls import path
from .views import (
    create_software_assignment,
    list_software_assignments,
    get_software_assignment,
    update_software_assignment,
    delete_software_assignment,
    view_file,
    get_assignment_history
)

from django.urls import path
from . import views

urlpatterns = [
    # Create
    path('software-assignment/create/', views.create_software_assignment, name='create_software_assignment'),

    # List all assignments
    path('software-assignments/', views.list_software_assignments, name='list_software_assignments'),

    # Retrieve single assignment with history
    path('software-assignment/<int:assignment_id>/', views.get_software_assignment, name='get_software_assignment'),

    # Update
    path('software-assignment/<int:assignment_id>/update/', views.update_software_assignment, name='update_software_assignment'),

    # Delete
    path('software-assignment/<int:assignment_id>/delete/', views.delete_software_assignment, name='delete_software_assignment'),

    # Get assignment history
    path('software-assignment/<int:assignment_id>/history/', views.get_assignment_history, name='get_assignment_history'),

    # Download file
    path('software-assignment/view_file/', views.view_file, name='view_file'),
]
