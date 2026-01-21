from django.urls import path
from . import views

urlpatterns = [
    # --- Hardware Assignment CRUD URLs ---
    path('hardware-assignments/', views.list_hardware_assignments, name='list_hardware_assignments'),
    path('hardware-assignments/create/', views.create_hardware_assignment, name='create_hardware_assignment'),
    path('hardware-assignments/<int:assignment_id>/', views.get_hardware_assignment, name='get_hardware_assignment'),
    path('hardware-assignments/<int:assignment_id>/update/', views.update_hardware_assignment, name='update_hardware_assignment'),
    path('hardware-assignments/<int:assignment_id>/delete/', views.delete_hardware_assignment, name='delete_hardware_assignment'),
    path('download-file/', views.download_file, name='download-file')
]
