from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import TravelRequest
from .serializers import TravelRequestSerializer
from travel_request.utils.exceptions import TravelRequestException
from travel_request.utils.approval_history_service import log_approval_action
from roboxa_technologies.utils.project_email_resolver import ProjectApprovalResolver
from roboxa_technologies.utils.email_utils import send_approval_mail


# =================================================
# CREATE
# =================================================
class TravelRequestCreateAPIView(generics.CreateAPIView):
    queryset = TravelRequest.objects.all()
    serializer_class = TravelRequestSerializer


# =================================================
# LIST ALL
# =================================================
class TravelRequestListAPIView(generics.ListAPIView):
    serializer_class = TravelRequestSerializer

    def get_queryset(self):
        return TravelRequest.objects.all().order_by("-request_id")


# =================================================
# LIST BY EMPLOYEE CODE
# =================================================
class TravelRequestByEmployeeCodeAPIView(generics.ListAPIView):
    serializer_class = TravelRequestSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "employee_code",
                openapi.IN_QUERY,
                description="Employee code to fetch all travel requests",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        employee_code = request.query_params.get("employee_code")

        if not employee_code:
            raise TravelRequestException("employee_code is required")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return TravelRequest.objects.filter(
            employee_code=self.request.query_params.get("employee_code")
        ).order_by("-request_id")


# =================================================
# GET BY REQUEST ID
# =================================================
class TravelRequestDetailByRequestIdAPIView(generics.RetrieveAPIView):
    queryset = TravelRequest.objects.all()
    serializer_class = TravelRequestSerializer
    lookup_field = "request_id"


# =================================================
# UPDATE (EDIT)
# =================================================
class TravelRequestEditAPIView(generics.UpdateAPIView):
    queryset = TravelRequest.objects.all()
    serializer_class = TravelRequestSerializer
    lookup_field = "request_id"
    http_method_names = ["patch"]  # PATCH only (recommended)


# =================================================
# APPROVE / REJECT
# =================================================
class TravelRequestActionAPIView(APIView):
    """
    Unified API for APPROVE / REJECT
    (PM / DELIVERY / SBU)
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["action", "level"],
            properties={
                "action": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["APPROVE", "REJECT"],
                ),
                "level": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["PM", "DELIVERY", "SBU"],
                ),
                "remarks": openapi.Schema(
                    type=openapi.TYPE_STRING,
                ),
            },
        )
    )
    def post(self, request, request_id):

        action = request.data.get("action")
        level = request.data.get("level")
        remarks = request.data.get("remarks", "")

        if action not in ["APPROVE", "REJECT"]:
            raise TravelRequestException("Invalid action")

        if level not in ["PM", "DELIVERY", "SBU"]:
            raise TravelRequestException("Invalid level")

        try:
            tr = TravelRequest.objects.get(request_id=request_id)
        except TravelRequest.DoesNotExist:
            raise TravelRequestException("Request not found", status_code=404)

        expected_status = {
            "PM": "Submitted",
            "DELIVERY": "PM Approved",
            "SBU": "Delivery Approved",
        }

        if tr.status != expected_status[level]:
            raise TravelRequestException(
                f"Invalid state for {level} action"
            )

        # ---- UPDATE STATUS ----
        if action == "APPROVE":
            tr.status = {
                "PM": "PM Approved",
                "DELIVERY": "Delivery Approved",
                "SBU": "SBU Approved",
            }[level]
        else:
            tr.status = "Rejected"

        tr.save()

        # ---- APPROVAL HISTORY ----
        log_approval_action(
            travel_request=tr,
            level=level,
            action="APPROVED" if action == "APPROVE" else "REJECTED",
            action_by=request.user.name,
            remarks=remarks,
        )

        # ---- EMAIL FLOW ----
        emails = ProjectApprovalResolver.get_approver_emails(tr.project_code)
        employee_email = tr.personaldetails.email

        if action == "APPROVE":
            send_approval_mail(
                subject=f"Travel Request Update - {tr.request_id}",
                message=f"Your travel request {tr.request_id} has been approved by {level}.",
                recipients=[employee_email],
            )

            next_email = {
                "PM": emails.get("delivery_manager"),
                "DELIVERY": emails.get("sbu_head"),
            }.get(level)

            if next_email:
                send_approval_mail(
                    subject=f"Approval Required - {tr.request_id}",
                    message="A new travel request is awaiting your approval.",
                    recipients=[next_email],
                )
        else:
            send_approval_mail(
                subject=f"Travel Request Rejected - {tr.request_id}",
                message=f"Rejected by {level}. Reason: {remarks}",
                recipients=[employee_email],
            )

        return Response(
            {"message": f"{action} processed for {level}"},
            status=status.HTTP_200_OK,
        )
