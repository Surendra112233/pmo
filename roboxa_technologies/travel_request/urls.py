# travel/urls.py
from django.urls import path
from .views import (
    TravelRequestByEmployeeCodeAPIView,
    TravelRequestCreateAPIView,
    TravelRequestDetailByRequestIdAPIView,
    TravelRequestEditAPIView,
    TravelRequestListAPIView,
    TravelRequestActionAPIView,        # ✅ ADD
    
)

urlpatterns = [
    # CREATE travel request
    path(
        'api/travel-request/',
        TravelRequestCreateAPIView.as_view(),
        name='create-travel-request'
    ),

    # LIST all travel requests
    path(
        'api/travel-request/all/',
        TravelRequestListAPIView.as_view(),
        name='list-travel-requests'
    ),

    # GET requests by employee_code
    path(
        'api/travel-request/by-employee/',
        TravelRequestByEmployeeCodeAPIView.as_view(),
        name='travel-request-by-employee'
    ),

    # GET single request by request_id
    path(
        'api/travel-request/<str:request_id>/',
        TravelRequestDetailByRequestIdAPIView.as_view(),
        name='travel-request-detail'
    ),

    # UPDATE request (only if rejected)
    path(
        'api/travel-request/<int:request_id>/edit/',
        TravelRequestEditAPIView.as_view(),
        name='edit-travel-request'
    ),

    # 🔥 SINGLE UNIFIED APPROVE / REJECT API
    path(
        'api/travel-request/<int:request_id>/action/',
        TravelRequestActionAPIView.as_view(),
        name='travel-request-action'
    ),

    # 📜 GET APPROVAL HISTORY (Timeline)
    # path(
    #     'api/travel-request/<int:request_id>/approval-history/',
    #     ApprovalHistoryAPIView.as_view(),
    #     name='travel-request-approval-history'
    # ),
]
