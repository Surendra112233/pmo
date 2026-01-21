
from django.urls import path
from . import views

urlpatterns = [
    path('create_user/', views.create_user, name='create_user'),
    path('edit_user/<str:user_id>/', views.edit_user, name='edit_user'),
    path('get_users/', views.maintain_users, name='maintain_users'),
    path('get_users/<str:user_id>/', views.get_user_by_id, name='maintain_users_byid'),
    path('delete_user/<str:user_id>/',views.delete_user,name='delete_user_byid'),
    path('user_role_assign/', views.assign_or_update_user_roles, name='user_role_assign'),
    path('edit_user_role_assign/<str:user_id>/', views.edit_user_assign_roles, name='edit_user_role_assign'),
    path('get_user_role_assignments/', views.get_user_role_assignments, name='get_user_role_assignments'),
    path('get_user_role_assign_byid/<str:user_id>/', views.get_user_role_assignment_by_id, name='get_user_role_assignments_byid'),
    path('delete_user_role_assign/<str:user_id>/', views.delete_user_role_assignment, name='delete_user_role_assign'),
    path('create_role/',views.create_role, name='create_role'),
    path('edit_role/<int:role_id>/', views.edit_role, name='edit_role'),
    path('get_roles/',views.get_roles, name='maintain_role'),
    path('get_role_byid/<int:role_id>/',views.get_role_by_id, name='get_role_byid')
]
