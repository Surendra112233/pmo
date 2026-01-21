from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone
from mimetypes import guess_type

import os
from urllib.parse import unquote, urlparse
from django.conf import settings

from .models import SoftwareAssignment, SoftwareAssignmentHistory
from .serializers import SoftwareAssignmentSerializer, SoftwareAssignmentUpdateSerializer
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponse


# ---------------- CREATE SOFTWARE ASSIGNMENT ----------------
@swagger_auto_schema(method='post', request_body=SoftwareAssignmentSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def create_software_assignment(request):
    serializer = SoftwareAssignmentSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        current_user_email = (
            getattr(request.user, 'email', None)
            or request.data.get('admin_user_name')
            or 'system'
        )

        assignment = serializer.save(last_changed_by=current_user_email)

        from_date = serializer.validated_data.get('from_date') or timezone.localtime(timezone.now()).date()

        SoftwareAssignmentHistory.objects.create(
            assignment=assignment,
            status=assignment.status,
            user_name=assignment.user_name,
            from_date=from_date,
            to_date=None,
            last_changed_by=current_user_email
        )
        response_data = SoftwareAssignmentSerializer(assignment, context={'request': request}).data

        return Response({
            "message": "Software assignment created successfully.",
            "data": response_data
        }, status=status.HTTP_201_CREATED)

    error_message = next(iter(serializer.errors.values()))[0]

    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )



# ---------------- LIST ALL SOFTWARE ASSIGNMENTS ----------------
@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([AllowAny])
def list_software_assignments(request):
    assignments = SoftwareAssignment.objects.all().order_by('-created_at')
    serializer = SoftwareAssignmentSerializer(assignments, many=True, context={'request': request})
    return Response({"data": serializer.data})


# ---------------- RETRIEVE SOFTWARE ASSIGNMENT WITH HISTORY ----------------
@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([AllowAny])
def get_software_assignment(request, assignment_id):
    assignment = get_object_or_404(SoftwareAssignment, id=assignment_id)
    serializer = SoftwareAssignmentSerializer(assignment, context={'request': request})

    histories = assignment.history.all().order_by('-from_date', '-last_changed_datetime')

    return Response({
        "data": serializer.data,
        "Assignment_Details": [
            {
                "status": h.status,
                "user_name": h.user_name,
                "from_date": h.from_date,
                "to_date": h.to_date,
                "last_changed_by": h.last_changed_by,
                "timestamp": h.last_changed_datetime
            }
            for h in histories
        ]
    })


# ---------------- UPDATE SOFTWARE ASSIGNMENT ----------------
@swagger_auto_schema(method='put', request_body=SoftwareAssignmentUpdateSerializer)
@api_view(['PUT'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def update_software_assignment(request, assignment_id):
    assignment = get_object_or_404(SoftwareAssignment, id=assignment_id)
    old_user = assignment.user_name
    old_status = assignment.status
    old_changed_by = assignment.last_changed_by

    serializer = SoftwareAssignmentUpdateSerializer(
        assignment, data=request.data, partial=True, context={'request': request}
    )

    if serializer.is_valid():
        current_user_email = (
            getattr(request.user, 'email', None)
            or request.data.get('admin_user_name')
            or assignment.last_changed_by
        )

        updated_assignment = serializer.save(last_changed_by=current_user_email)

        from_date = serializer.validated_data.get('from_date') or timezone.localtime(timezone.now()).date()

        # HISTORY LOGIC
        if old_user != updated_assignment.user_name or old_status != updated_assignment.status or old_changed_by != current_user_email:
            active_history = SoftwareAssignmentHistory.objects.filter(
                assignment=assignment, to_date__isnull=True
            ).first()
            if active_history:
                active_history.to_date = from_date
                active_history.save()

            SoftwareAssignmentHistory.objects.create(
                assignment=assignment,
                status=updated_assignment.status,
                user_name=updated_assignment.user_name,
                from_date=from_date,
                to_date=None,
                last_changed_by=current_user_email
            )

        histories = assignment.history.all().order_by('-from_date', '-last_changed_datetime')

        return Response({
            "message": "Software assignment updated successfully.",
            "data": SoftwareAssignmentSerializer(updated_assignment, context={'request': request}).data,
            "Assignment_Details": [
                {
                    "status": h.status,
                    "user_name": h.user_name,
                    "from_date": h.from_date,
                    "to_date": h.to_date,
                    "last_changed_by": h.last_changed_by,
                    "timestamp": h.last_changed_datetime
                }
                for h in histories
            ]
        })
    error_message = next(iter(serializer.errors.values()))[0]

    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )


# ---------------- DELETE SOFTWARE ASSIGNMENT ----------------
@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_software_assignment(request, assignment_id):
    assignment = get_object_or_404(SoftwareAssignment, id=assignment_id)
    assignment.delete()
    return Response({"message": "Deleted successfully."})



# ---------------- GET ASSIGNMENT HISTORY ----------------
@swagger_auto_schema(method='get')
@api_view(['GET'])
@permission_classes([AllowAny])
def get_assignment_history(request, assignment_id):
    assignment = get_object_or_404(SoftwareAssignment, id=assignment_id)
    histories = assignment.history.all().order_by('-from_date', '-last_changed_datetime')

    return Response({
        "assignment_id": assignment.id,
        "Assignment_Details": [
            {
                "status": h.status,
                "user_name": h.user_name,
                "from_date": h.from_date,
                "to_date": h.to_date,
                "last_changed_by": h.last_changed_by,
                "timestamp": h.last_changed_datetime
            }
            for h in histories
        ]
    })
#views_file


# ---------------- VIEW FILE (IMAGE / INVOICE) ----------------
@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'file_url',
            openapi.IN_QUERY,
            description="Full file URL returned by image_url or invoice_url",
            type=openapi.TYPE_STRING,
            required=True
        )
    ]
)
@api_view(['GET'])
@permission_classes([AllowAny])
def view_file(request):
    file_url = request.GET.get('file_url')

    if not file_url:
        return Response(
            {"message": "file_url is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    parsed = urlparse(unquote(file_url))

    #  THIS IS THE FIX
    relative_path = parsed.path.lstrip('/')  # remove leading /
    file_path = os.path.join(settings.BASE_DIR, relative_path)

    if not os.path.exists(file_path):
        return Response(
            {
                "message": "File not found.",
                "debug": file_path
            },
            status=status.HTTP_404_NOT_FOUND
        )

    content_type, _ = guess_type(file_path)

    response = FileResponse(
        open(file_path, 'rb'),
        content_type=content_type or 'application/octet-stream'
    )

    #  open in browser tab
    response['Content-Disposition'] = 'inline'

    return response