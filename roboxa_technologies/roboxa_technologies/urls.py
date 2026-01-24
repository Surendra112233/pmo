"""
URL configuration for roboxa_technologies project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# roboxa_technologies/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


# Set up the schema view for Swagger and Redoc with JWT token auth support
schema_view = get_schema_view(
    openapi.Info(
        title="MY Own Roboxa Technologies API",
        default_version='v1',
        description="My Own API documentation for Roboxa Technologies project",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=[],  # Empty so Swagger UI doesn't break
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', include('management.urls')),
    path('user_management/', include('user_management.urls')),
    path('master_data/', include('master_data.urls')),
    path('pmo/', include('pmo.urls')),
    path('employee/', include('employee.urls')),
    path('manager/', include('manager.urls')),
    # path('emp_management/', schema_view.with_ui('swagger')),
    path('emp_management/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('Assets/', include('Assets.urls')),
    path('travel_request', include('travel_request.urls')),

    path('software/',include('software.urls')),
    path('emp_management/', schema_view.with_ui('swagger')),
    #path('emp_management/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('inventory/', include('inventory.urls')),
    
]



