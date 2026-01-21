from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import Http404, FileResponse
import os
from urllib.parse import unquote
from django.db import transaction  # ADD THIS IMPORT

from .models import HardwareAssignment, AssignmentHistory
from .serializers import HardwareAssignmentSerializer, HardwareAssignmentUpdateSerializer


def get_user_email_from_request(request):
    """
    Extract user email from JWT token in the request
    """
    if request.user and request.user.is_authenticated:
        if hasattr(request.user, 'email') and request.user.email:
            return request.user.email
        elif '@' in request.user.username:
            return request.user.username
        else:
            return f"{request.user.username}@roboxaservices.com"
    return 'system@roboxaservices.com'


# ------------------- Create Hardware Assignment -------------------
@swagger_auto_schema(
    method='post',
    request_body=HardwareAssignmentSerializer,
    operation_description="Create a new hardware assignment. The authenticated user's email will be used as last_changed_by.",
    responses={
        201: openapi.Response("Hardware assignment created successfully", HardwareAssignmentSerializer),
        400: "Bad request",
        401: "Unauthorized"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic  # ADD TRANSACTION ATOMIC
def create_hardware_assignment(request):
    # Get user email from JWT token
    user_email = get_user_email_from_request(request)
    
    # Create a copy of request data
    data = request.data.copy()
    # Force the last_changed_by to be the authenticated user's email
    data['last_changed_by'] = user_email
    
    serializer = HardwareAssignmentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        # Get manual from_date if given, otherwise today (EXACT SOFTWARE CODE LOGIC)
        from_date = serializer.validated_data.get('from_date') or timezone.localtime(timezone.now()).date()
        
        assignment = serializer.save(last_changed_by=user_email)

        # Create initial assignment history record with proper from_date
        AssignmentHistory.objects.create(
            hardware_assignment=assignment,
            user_name=assignment.user_name,
            status=assignment.status,
            from_date=from_date,  # Use the calculated from_date
            to_date=None,
            changed_by=user_email
        )

        # Get assignment history for response
        histories = assignment.assignment_history.all().order_by('-from_date')
        history_data = [
            {
                "status": h.status,
                "user_name": h.user_name,
                "from_date": h.from_date,
                "to_date": h.to_date,
                "last_changed_by": h.changed_by,
                "changed_datetime": h.changed_datetime
            }
            for h in histories
        ]

        response_data = HardwareAssignmentSerializer(assignment, context={'request': request}).data
        

        return Response(
            {
                "message": "Hardware assignment created successfully.",
                "authenticated_user": user_email,
                "data": response_data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]

    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )



# ------------------- List All Hardware Assignments -------------------
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all hardware assignments.",
    responses={200: openapi.Response("List of hardware assignments", HardwareAssignmentSerializer(many=True))}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_hardware_assignments(request):
    # Order by latest first (descending order)
    assignments = HardwareAssignment.objects.all().order_by('-created_at')  # Add minus sign for descending
   
    # Alternative: You can also order by '-id' if you want newest ID first
    # assignments = HardwareAssignment.objects.all().order_by('-id')
   
    response_data = []
    for assignment in assignments:
        assignment_data = HardwareAssignmentSerializer(assignment, context={'request': request}).data
       
        # No need to manually add history here, it's already in serializer's to_representation
       
        response_data.append(assignment_data)
   
    return Response(
        {
            "message": "Hardware assignments retrieved successfully.",
            "authenticated_user": get_user_email_from_request(request),
            "data": response_data
        },
        status=status.HTTP_200_OK
    )
 
 
# ------------------- Get Hardware Assignment by ID -------------------
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a hardware assignment by ID.",
    responses={200: HardwareAssignmentSerializer, 404: "Not found"}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_hardware_assignment(request, assignment_id):
    try:
        user_email = get_user_email_from_request(request)
        
        assignment = HardwareAssignment.objects.get(id=assignment_id)
        serializer = HardwareAssignmentSerializer(assignment, context={'request': request})
        
        histories = assignment.assignment_history.all().order_by('-from_date')
        history_data = [
            {
                "status": h.status,
                "user_name": h.user_name,
                "from_date": h.from_date,
                "to_date": h.to_date,
                "last_changed_by": h.changed_by,
                "changed_datetime": h.changed_datetime
            }
            for h in histories
        ]
        
        response_data = serializer.data
        
        
        return Response(
            {
                "message": "Hardware assignment retrieved successfully.", 
                "authenticated_user": user_email,
                "data": response_data
            },
            status=status.HTTP_200_OK
        )
    except HardwareAssignment.DoesNotExist:
        return Response({"message": "Hardware assignment not found."}, status=status.HTTP_404_NOT_FOUND)


# ------------------- Update Hardware Assignment -------------------
@swagger_auto_schema(
    method='put',
    request_body=HardwareAssignmentUpdateSerializer,
    operation_description="Update a hardware assignment by ID (partial update allowed). The authenticated user's email will be used as last_changed_by and in assignment history.",
    responses={
        200: openapi.Response("Hardware assignment updated successfully", HardwareAssignmentUpdateSerializer),
        400: "Bad request",
        401: "Unauthorized",
        404: "Not found"
    }
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic  # ADD TRANSACTION ATOMIC
def update_hardware_assignment(request, assignment_id):
    # Get user email from JWT token
    user_email = get_user_email_from_request(request)
    
    assignment = get_object_or_404(HardwareAssignment, id=assignment_id)
    old_user = assignment.user_name
    old_status = assignment.status
    old_changed_by = assignment.last_changed_by  # ADD THIS LIKE SOFTWARE CODE

    # Create a copy of request data
    data = request.data.copy()
    # Force the last_changed_by to be the authenticated user's email
    data['last_changed_by'] = user_email

    serializer = HardwareAssignmentUpdateSerializer(
        assignment,
        data=data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        # Get email from logged-in user (EXACT SOFTWARE CODE LOGIC)
        current_user_email = (
            getattr(request.user, 'email', None) or
            request.data.get('admin_user_name') or
            assignment.last_changed_by
        )

        # Get manual from_date if given, otherwise today (EXACT SOFTWARE CODE LOGIC)
        from_date = serializer.validated_data.get('from_date') or timezone.localtime(timezone.now()).date()

        # EXACT SOFTWARE HISTORY LOGIC — create new history if:
        # user_name changed OR status changed OR updated by a different user
        if (
            old_user != serializer.validated_data.get('user_name', old_user)
            or old_status != serializer.validated_data.get('status', old_status)
            or old_changed_by != current_user_email  # ADD THIS CHECK LIKE SOFTWARE CODE
        ):
            # EXACT SOFTWARE CODE: Close previous open record
            active_history = AssignmentHistory.objects.filter(
                hardware_assignment=assignment, 
                to_date__isnull=True
            ).first()

            if active_history:
                # CRITICAL FIX: Set the previous record's to_date to the NEW from_date
                active_history.to_date = from_date
                active_history.save()

            # EXACT SOFTWARE CODE: Create new history record
            AssignmentHistory.objects.create(
                hardware_assignment=assignment,
                user_name=serializer.validated_data.get('user_name', old_user),
                status=serializer.validated_data.get('status', old_status),
                from_date=from_date,
                to_date=None,  # Current assignment has no end date
                changed_by=current_user_email
            )

        # Now save the assignment after handling history
        updated_assignment = serializer.save(last_changed_by=current_user_email)

        # Get updated assignment history
        histories = assignment.assignment_history.all().order_by('-from_date')
        history_data = [
            {
                "status": h.status,
                "user_name": h.user_name,
                "from_date": h.from_date,
                "to_date": h.to_date,
                "last_changed_by": h.changed_by,
                "changed_datetime": h.changed_datetime
            }
            for h in histories
        ]

        # Prepare response data with history
        response_data = HardwareAssignmentUpdateSerializer(updated_assignment, context={'request': request}).data
        

        return Response(
            {
                "message": "Hardware assignment updated successfully.",
                "authenticated_user": user_email,
                "data": response_data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]

    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )



# ------------------- Delete Hardware Assignment -------------------
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a hardware assignment by ID.",
    responses={
        200: "Hardware assignment deleted successfully", 
        401: "Unauthorized",
        404: "Not found"
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_hardware_assignment(request, assignment_id):
    try:
        user_email = get_user_email_from_request(request)
        
        assignment = HardwareAssignment.objects.get(id=assignment_id)
        assignment.delete()
        return Response(
            {
                "message": "Hardware assignment deleted successfully.",
                "authenticated_user": user_email
            }, 
            status=status.HTTP_200_OK
        )
    except HardwareAssignment.DoesNotExist:
        return Response({"message": "Hardware assignment not found."}, status=status.HTTP_404_NOT_FOUND)


# ------------------- View File -------------------
@swagger_auto_schema(method='get', manual_parameters=[
    openapi.Parameter("file_path", openapi.IN_QUERY, description="Full path of file", type=openapi.TYPE_STRING, required=True)
])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_file(request):
    file_path = request.query_params.get('file_path')
    if not file_path:
        return Response({"message": "file_path is required."}, status=status.HTTP_400_BAD_REQUEST)
   
    # Unquote the URL first
    file_path = unquote(file_path)
   
    # Check if it's a full URL and extract just the path portion
    if file_path.startswith('http://'):
        # Remove protocol and domain, keep only the path
        parts = file_path.split('/', 3)  # Split at most 3 times
        if len(parts) > 3:
            file_path = '/' + parts[3]  # Get everything after domain
        else:
            file_path = '/'
   
    # Convert to absolute path
    file_path = os.path.abspath(file_path.lstrip('/'))
   
    # Rest of your code remains exactly the same...
    if not os.path.exists(file_path):
        return Response({"message": "File not found."}, status=status.HTTP_404_NOT_FOUND)
   
    # Get the filename
    filename = os.path.basename(file_path)
   
    # Determine file type from extension
    file_extension = os.path.splitext(filename)[1].lower()
   
    # Simple content type mapping
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
    }
   
    # Get content type, default to generic binary
    content_type = content_types.get(file_extension, 'application/octet-stream')
   
    # Create response WITHOUT as_attachment
    response = FileResponse(open(file_path, 'rb'), filename=filename)
    response['Content-Type'] = content_type
   
    return response