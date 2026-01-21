from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import TimesheetApproval, Project
from employee.models import EmployeeTimesheet
from master_data.models import ProjectTasks,Employee
from employee.serializers import EmployeeTimesheetSerializer
from manager.serializers import TimesheetApprovalSerializer
from .serializers import TimesheetApprovalSerializer
from datetime import timedelta,date
from django.db.models import Sum
from django.db import transaction
from django.db.models import Q
from django.db import models
from pmo.models import Project,ProjectTeam,PhaseAllocation,ProjectTeamAllocation
from django.core.mail import send_mail
from django.conf import settings
from user_management.models import UserProfile,UserRoleAssign
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from datetime import datetime, timedelta, date
import calendar
import numpy as np
from django.db.models import Sum, Min, Max
from collections import defaultdict



def convert_timedelta_to_hours(time_value):
    """Converts timedelta to hours (float)"""
    if isinstance(time_value, timedelta):
        return round(time_value.total_seconds() / 3600, 2)  # Convert seconds to hours
    return round(time_value, 2) if time_value else 0

def get_working_days(start_date, end_date):
    working_days = 0
    current_day = start_date
    while current_day <= end_date:
        if current_day.weekday() < 5:  # 0=Monday, ..., 6=Sunday
            working_days += 1
        current_day += timedelta(days=1)
    return working_days

def get_total_worked_hours(project_code):
        total_time = EmployeeTimesheet.objects.filter(
            project_code=project_code, 
            status="approved"
        ).aggregate(Sum("worked_hours"))["worked_hours__sum"]

        if total_time is None:
            return "00:00"  # Default if no worked hours

        if isinstance(total_time, timedelta):
            total_seconds = int(total_time.total_seconds())  # Convert to seconds
        elif isinstance(total_time, (float, int)):  # If stored as float hours
            total_seconds = int(total_time * 3600)
        else:
            raise ValueError(f"Unexpected data type for total_worked_hours: {type(total_time)}")

        # Convert total seconds to HH:MM format
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{hours:02}:{minutes:02}"  # Exclude seconds

#get timesheet for approve all
@swagger_auto_schema(
    method='post',
    operation_description="Fetch the timesheet entries for a specific project, status, month, year, and optionally an employee using request body.",
    responses={200: openapi.Response("Timesheet entries retrieved successfully.", EmployeeTimesheetSerializer(many=True))},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_code': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
            'employee_code': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
            'status': openapi.Schema(
                type=openapi.TYPE_ARRAY, 
                items=openapi.Schema(type=openapi.TYPE_STRING),
                default=["open"]
            ),
            'month': openapi.Schema(type=openapi.TYPE_INTEGER),
            'year': openapi.Schema(type=openapi.TYPE_INTEGER)
        },
    ),
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_timesheet_for_approval(request):
    project_code = request.data.get('project_code', '').strip()
    employee_code = request.data.get('employee_code', '').strip()
    status_filter = request.data.get('status', [])  # Default to empty list
    month = request.data.get('month')
    year = request.data.get('year')
    total_worked_hours = get_total_worked_hours(project_code)

    VALID_STATUSES = {"open", "approved", "rejected"}
    

    # Convert status to a list if it's a string
    if isinstance(status_filter, str):
        status_filter = [status_filter]

    # If status is empty, set default to ["open", "approved"]
    if not status_filter:
        status_filter = ["open", "approved"]
    else:
        status_filter = [s for s in status_filter if s in VALID_STATUSES]  # Filter valid statuses

    # Fetch project details
    try:
        project = Project.objects.get(project_code=project_code)
    except Project.DoesNotExist:
        return Response({"message": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    # Build query filter
    timesheet_filter = {
        "project_code": project_code,
        "status__in": status_filter,
        "month": month,
        "year": year,
    }

    if employee_code:
        timesheet_filter["employee_code"] = employee_code

    timesheet_entries = EmployeeTimesheet.objects.filter(**timesheet_filter)

    # Serialize timesheet data
    serialized_timesheets = EmployeeTimesheetSerializer(timesheet_entries, many=True).data
    
    # Inject `role_name` into each entry
    for i, entry in enumerate(serialized_timesheets):
        emp_code = entry.get("employee_code")
        try:
            user = UserProfile.objects.get(user_id=emp_code)
            role_assignment = UserRoleAssign.objects.filter(user_id=user).first()
            roles = role_assignment.role_name if role_assignment else []
        except UserProfile.DoesNotExist:
            roles = []
        
        serialized_timesheets[i]["delivery_head"] = project.delivery_head if project.delivery_head else None
        serialized_timesheets[i]["management"] = project.management if project.management else None
        serialized_timesheets[i]["role_name"] = roles


    response_data = {
    "budgeted_hours": project.allocated_budgeted_hours,
    "allocated_hours": project.allocated_hours,
    "total_worked_hours": total_worked_hours,
    "timesheet_entries": serialized_timesheets
}

    return Response(response_data, status=status.HTTP_200_OK)

#get tiemsheet approval for all projects and employees
@swagger_auto_schema(
    method='post',
    operation_description="Fetch timesheet entries with project and employee filters.",
    responses={200: openapi.Response("Timesheet entries retrieved successfully.", EmployeeTimesheetSerializer(many=True))},
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'project_code': openapi.Schema(type=openapi.TYPE_STRING),
            'employee_code': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
            'status': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                default=["open"]
            ),
            'month': openapi.Schema(type=openapi.TYPE_INTEGER),
            'year': openapi.Schema(type=openapi.TYPE_INTEGER)
        },
    ),
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_timesheet_for_approval_all(request):
    project_code = request.data.get('project_code', '').strip()
    employee_code = request.data.get('employee_code', '').strip()
    status_filter = request.data.get('status', []) or ["open"]
    month = request.data.get('month')
    year = request.data.get('year')

    VALID_STATUSES = {"open", "approved", "rejected"}

    if isinstance(status_filter, str):
        status_filter = [status_filter]
    status_filter = [s for s in status_filter if s in VALID_STATUSES]

    # Base query filter
    timesheet_filter = {
        "status__in": status_filter,
        "month": month,
        "year": year
    }
    if project_code:
        timesheet_filter["project_code__project_code"] = project_code
    if employee_code:
        timesheet_filter["employee_code__employee_code"] = employee_code


    timesheet_entries = EmployeeTimesheet.objects.filter(**timesheet_filter).select_related("project_code")

    # Serialize entries
    serialized_timesheets = EmployeeTimesheetSerializer(timesheet_entries, many=True).data

    for i, entry in enumerate(serialized_timesheets):
        emp_code = entry.get("employee_code")
        proj_code = entry.get("project_code")

        # Add project_name
        try:
            project = Project.objects.get(project_code=proj_code)
            serialized_timesheets[i]["project_name"] = project.project_description
            serialized_timesheets[i]["delivery_head"] = project.delivery_head
            serialized_timesheets[i]["management"] = project.management
        except Project.DoesNotExist:
            serialized_timesheets[i]["project_name"] = None
            serialized_timesheets[i]["delivery_head"] = None
            serialized_timesheets[i]["management"] = None

        # Add role name
        try:
            user = UserProfile.objects.get(user_id=emp_code)
            role_assignment = UserRoleAssign.objects.filter(user_id=user).first()
            roles = role_assignment.role_name if role_assignment else []
        except UserProfile.DoesNotExist:
            roles = []

        serialized_timesheets[i]["role_name"] = roles

    if project_code:
        try:
            project = Project.objects.get(project_code=project_code)
        except Project.DoesNotExist:
            pass

    return Response({

        "timesheet_entries": serialized_timesheets
    }, status=status.HTTP_200_OK)


# Approve or reject timesheets in bulk
@swagger_auto_schema(
    method='put',
    operation_description="Approve or Reject timesheets in bulk or individually.",
    request_body=openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['approved', 'rejected']),
                'comments': openapi.Schema(type=openapi.TYPE_STRING, default=""),
                'project_code': openapi.Schema(type=openapi.TYPE_STRING, description="Project code"),
                'employee_code': openapi.Schema(type=openapi.TYPE_STRING, description="Employee code"),
                'timesheet_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="Timesheet ID")
            }
        )
    ),
    responses={
        200: openapi.Response("Timesheets updated successfully.", TimesheetApprovalSerializer(many=True)),
        400: "Invalid request parameters or validation errors.",
        404: "Timesheets not found for given employee and project."
    }
)
@api_view(["PUT"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def approve_or_reject_timesheet(request):
    """
    API to approve or reject timesheets in bulk or individually.
    """
    timesheet_requests = request.data

    if not isinstance(timesheet_requests, list) or not timesheet_requests:
        return Response(
            {"message": "Request body should be a non-empty list of timesheet objects."},
            status=status.HTTP_400_BAD_REQUEST
        )

    updated_timesheets = []

    with transaction.atomic():  # Ensures safe database transactions
        for timesheet_data in timesheet_requests:
            status_input = timesheet_data.get("status")
            comments = timesheet_data.get("comments", "").strip()
            project_code = timesheet_data.get("project_code")
            employee_code = timesheet_data.get("employee_code")
            timesheet_id = timesheet_data.get("timesheet_id")

            # Validate required fields
            if not project_code or not employee_code or timesheet_id is None:
                return Response(
                    {"message": "Missing required fields: project_code, employee_code, timesheet_id."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if status_input not in ["approved", "rejected"]:
                return Response(
                    {"message": "Invalid status. Use 'approved' or 'rejected'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if status_input == "rejected" and not comments:
                return Response(
                    {"message": "Comments are mandatory when rejecting timesheets."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Fetch the timesheet from TimesheetApproval or EmployeeTimesheet
                timesheet = (
                    TimesheetApproval.objects.filter(
                        Q(employee_code__employee_code=employee_code, project_code__project_code=project_code, id=timesheet_id)
                    ).first() or 
                    EmployeeTimesheet.objects.filter(
                        Q(employee_code__employee_code=employee_code, project_code__project_code=project_code, id=timesheet_id)
                    ).first()
                )

                if not timesheet:
                    return Response(
                        {"message": f"No matching timesheet found for ID {timesheet_id}."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Convert worked time to hours
                def convert_time_to_hours(worked_time):
                    """Convert worked time (HH:MM) to decimal hours"""
                    if isinstance(worked_time, timedelta):
                        return round(worked_time.total_seconds() / 3600, 2)
                    elif isinstance(worked_time, str):
                        try:
                            h, m = map(int, worked_time.split(':'))
                            return round(h + (m / 60), 2)
                        except ValueError:
                            return 0
                    elif isinstance(worked_time, (int, float)):
                        return float(worked_time)
                    return 0

                worked_hours = convert_time_to_hours(timesheet.worked_hours)
                booked_hours = convert_time_to_hours(timesheet.booked_hours)
                allocated_hours = float(timesheet.allocated_hours) if timesheet.allocated_hours else 0

                # Ensure correct comparison
                if booked_hours > allocated_hours:
                    return Response(
                        {"message": f"Booked hours exceed allocated hours for timesheet ID {timesheet_id}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if status_input == "approved" and timesheet.status == "rejected":
                    duplicate_in_approval = TimesheetApproval.objects.filter(
                        employee_code__employee_code=employee_code,
                        project_code__project_code=project_code,
                        date=timesheet.date
                    ).exclude(id=timesheet_id).exclude(status="rejected").exists()

                    duplicate_in_timesheet = EmployeeTimesheet.objects.filter(
                        employee_code__employee_code=employee_code,
                        project_code__project_code=project_code,
                        date=timesheet.date
                    ).exclude(id=timesheet_id).exclude(status="rejected").exists()

                    if duplicate_in_approval or duplicate_in_timesheet:
                        return Response(
                            {
                                "message": (
                                    f"Cannot approve rejected timesheet ID {timesheet_id} on {timesheet.date.strftime('%Y-%m-%d')}, "
                                    f"because another valid (non-rejected) entry already exists for the same date."
                                )
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )



                # Fetch Project budgeted hours (fetch once per loop)
                project_budgeted_hours = Project.objects.filter(project_code=timesheet.project_code).values_list('budgeted_hours', flat=True).first() or 0

                # Update or create record in TimesheetApproval
                timesheet_approval, _ = TimesheetApproval.objects.update_or_create(
                    id=timesheet.id,
                    defaults={
                        "employee_code": timesheet.employee_code,
                        "project_code": timesheet.project_code,
                        "status": status_input,
                        "comments": comments,
                        "month": timesheet.month,
                        "year": timesheet.year,
                        "budgeted_hours": project_budgeted_hours,
                        "allocated_hours": timesheet.allocated_hours if timesheet.allocated_hours is not None else 0,
                        "worked_hours": worked_hours,
                        "employee_name": timesheet.employee_name,
                        "date": timesheet.date,
                        "description": timesheet.description,
                        "project_role": timesheet.project_role,
                        "booked_hours": booked_hours if booked_hours is not None else 0,  #Ensure booked_hours is not null
                        "task_description": str(timesheet.task_description),
                        "remarks": timesheet.remarks or "",
                    }
                )

                # Update EmployeeTimesheet status
                EmployeeTimesheet.objects.filter(
                    employee_code__employee_code=employee_code,
                    project_code__project_code=project_code,
                    id=timesheet_id
                ).update(status=status_input)

                #  Automatically update PhaseAllocation worked_hours
                task_code = int(str(timesheet.task_description).split(" ")[0])

                if status_input == "approved":
                    update_phase_allocation_worked_hours(
                        project_code=project_code,
                        task_code = task_code
                    )

                updated_timesheets.append(timesheet_approval)
                # If the status is rejected, send an email to the employee
                if status_input == "rejected":
                    user_profile = UserProfile.objects.filter(user_id=employee_code).first()
                    if user_profile:
                        send_mail(
                        subject='Timesheet Rejected',
                        message=f"""Hi {user_profile.name},<br><br>

                    Your timesheet dated {timesheet.date.strftime('%d-%m-%Y')} for project <strong>{project_code}</strong> has been rejected.<br><br>

                    <strong>Comments:</strong> {comments}<br><br>

                    Best regards,<br>
                    <strong>ROBOXA PMO</strong>.
                    """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user_profile.email],
                        fail_silently=False,
                        html_message=f"""Dear {user_profile.name},<br><br>

                    Your timesheet dated {timesheet.date.strftime('%d-%m-%Y')} for project <strong>{project_code}</strong> has been rejected.<br><br>

                    <strong>Comments:</strong> {comments}<br><br>

                    Best regards,<br>
                    <strong>ROBOXA PMO</strong>.
                    """
                    )

            except Exception as e:
                return Response(
                    {"message": f"Error processing timesheet ID {timesheet_id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    serialized_timesheets = TimesheetApprovalSerializer(updated_timesheets, many=True).data

    # return Response(
    #     {"message": "Timesheets have been updated successfully.", "data": serialized_timesheets},
    #     status=status.HTTP_200_OK
    # )
    if all(ts.status == "approved" for ts in updated_timesheets):
        message = "Timesheet approved successfully."
    elif all(ts.status == "rejected" for ts in updated_timesheets):
        message = "Timesheet rejected successfully."
    else:
        message = "Timesheet processed successfully."

    return Response(
        {"message": message, "data": serialized_timesheets},
        status=status.HTTP_200_OK
    )


#get projectsummary
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
                description="List of Project Codes"
            )
        },
        required=["project_code"]
    ),
    operation_description="Fetch project summaries for multiple project codes.",
    responses={
        200: openapi.Response(
            "Project summaries retrieved successfully.",
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "project_code": openapi.Schema(type=openapi.TYPE_STRING, description="Project Code"),
                        "description": openapi.Schema(type=openapi.TYPE_STRING, description="Project Description"),
                        "project_status": openapi.Schema(type=openapi.TYPE_STRING, description="Current Project Status"),
                        "total_budgeted_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Budgeted Hours"),
                        "total_allocated_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Allocated Hours"),
                        "total_worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Worked Hours"),
                        "billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Billable Hours"),
                        "non_billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Non-Billable Hours"),
                        "utilization_percentage": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Utilization Percentage"),
                    }
                )
            )
        ),
        400: openapi.Response("Invalid request."),
        404: openapi.Response("One or more projects not found."),
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_summary(request):
    """Fetch project summaries for multiple project codes"""
    try:
        project_codes = request.data.get("project_code", [])

        if not project_codes or not isinstance(project_codes, list):
            return Response({"message": "Invalid request. Provide a list of project codes."}, status=status.HTTP_400_BAD_REQUEST)

        projects = Project.objects.filter(project_code__in=project_codes)

        if not projects.exists():
            return Response({"message": "Projects not found."}, status=status.HTTP_404_NOT_FOUND)

        response_data = []
        
        for project in projects:
            # Fetch approved timesheets for this project
            timesheet_data = EmployeeTimesheet.objects.filter(
                project_code=project.project_code,
                status="approved"  # Ensure only approved timesheets are considered
            )

            def convert_to_decimal_hours(time_value):
                if not time_value:
                    return 0
                return time_value.total_seconds() / 3600  # Convert seconds to hours


            # Calculate total worked hours
            total_worked_hours = sum(
                convert_to_decimal_hours(entry.worked_hours) for entry in timesheet_data
            )

            # Get total allocated hours from the Project model
            total_allocated_hours = convert_timedelta_to_hours(project.allocated_hours)
            budgted_hours = convert_timedelta_to_hours(project.budgeted_hours)

            # # Get billable and non-billable tasks
            # billable_tasks = set(ProjectTasks.objects.filter(billable="Yes").values_list('task_code', flat=True))
            # non_billable_tasks = set(ProjectTasks.objects.filter(billable="No").values_list('task_code', flat=True))

            # Calculate billable and non-billable hours
            # billable_hours = sum(
            #     convert_to_decimal_hours(entry.worked_hours)
            #     for entry in timesheet_data if entry.task_description_id in billable_tasks
            # )

            # non_billable_hours = sum(
            #     convert_to_decimal_hours(entry.worked_hours)
            #     for entry in timesheet_data if entry.task_description_id in non_billable_tasks
            # )
            billable_hours = 0
            non_billable_hours = 0

            for entry in timesheet_data:
                hours = convert_to_decimal_hours(entry.worked_hours)
                if entry.project_code.project_code == "RB001":
                    non_billable_hours += hours
                else:
                    billable_hours += hours



            # Compute utilization percentage (avoid division by zero)
            # utilization_percentage = round((total_worked_hours / budgted_hours  * 100) if budgted_hours else 0, 2)
            utilization_percentage = round((total_worked_hours / total_allocated_hours * 100) if total_allocated_hours else 0,1)
            response_data.append({
                "project_code": project.project_code,
                "project_country": project.project_country,
                "project_region": project.project_region,
                "description": project.project_description,
                "project_type": project.project_type,
                "delivery_model": project.delivery_model,
                "start_date": project.from_date,
                "end_date": project.to_date,
                "project_status": project.project_status,
                "total_budgeted_hours": project.allocated_budgeted_hours,
                "total_allocated_hours": total_allocated_hours,
                "total_worked_hours": round(total_worked_hours, 2),  
                "billable_hours": round(billable_hours, 2),
                "non_billable_hours": round(non_billable_hours, 2),
                "utilization_percentage": utilization_percentage,
            })

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#get project summary deatiled by tasks
@swagger_auto_schema(
    method='post',
    operation_description="Fetch project detailed summary for multiple project codes with timesheet, task, and phase data.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="List of project codes"
            )
        },
        required=["project_code"]
    ),
    responses={
        200: openapi.Response(
            "Project detailed summary retrieved successfully.",
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "project_code": openapi.Schema(type=openapi.TYPE_STRING, description="Project Code"),
                        "description": openapi.Schema(type=openapi.TYPE_STRING, description="Project Description"),
                        "project_status": openapi.Schema(type=openapi.TYPE_STRING, description="Current Project Status"),
                        "total_budgeted_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Budgeted Hours"),
                        "total_allocated_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Allocated Hours"),
                        "total_worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Worked Hours"),
                        "billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Billable Hours"),
                        "non_billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Non-Billable Hours"),
                        "total_utilization": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Utilization Percentage"),
                        "task_description": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Task-level breakdown with allocated and worked hours.",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "task_code": openapi.Schema(type=openapi.TYPE_INTEGER, description="Task Code"),
                                    "task_group": openapi.Schema(type=openapi.TYPE_STRING, description="Task Group"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Task Description"),
                                    "allocated_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Allocated Hours"),
                                    "worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Worked Hours"),
                                    "budgeted_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT),
                                    "phase_wise_utilization": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Utilization for this task/phase"),
                                    "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Phase Start Date"),  
                                    "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Phase End Date")     
                                    
                                }
                            )
                        ),
                    }
                )
            )
        ),
        400: openapi.Response("Invalid request body."),
        404: openapi.Response("Projects not found."),
    }
)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_detailed_summary(request):
    """Fetch project detailed summary for multiple project codes"""
    data = request.data
    project_codes = data.get("project_code", [])

    if not project_codes or not isinstance(project_codes, list):
        return Response({"message": "Invalid request. 'project_code' should be a list of project codes."}, status=status.HTTP_400_BAD_REQUEST)

    projects = Project.objects.filter(project_code__in=project_codes)

    if not projects.exists():
        return Response({"message": "Projects not found."}, status=status.HTTP_404_NOT_FOUND)

    response_data = []

    for project in projects:
        timesheet_data = EmployeeTimesheet.objects.filter(project_code=project.project_code, status='approved')

        total_allocated_hours = convert_timedelta_to_hours(project.allocated_hours)
        budgeted_hours = convert_timedelta_to_hours(project.budgeted_hours)
        total_worked_hours = convert_timedelta_to_hours(timesheet_data.aggregate(Sum('worked_hours'))['worked_hours__sum'])

        # billable_tasks = ProjectTasks.objects.filter(billable="Yes").values_list('task_code', flat=True)
        # non_billable_tasks = ProjectTasks.objects.filter(billable="No").values_list('task_code', flat=True)

        # billable_hours = convert_timedelta_to_hours(timesheet_data.filter(task_description_id__in=billable_tasks).aggregate(Sum('worked_hours'))['worked_hours__sum'])
        # non_billable_hours = convert_timedelta_to_hours(timesheet_data.filter(task_description_id__in=non_billable_tasks).aggregate(Sum('worked_hours'))['worked_hours__sum'])
        # Billable: Approved hours where project_code != 'RB001'
        billable_hours = convert_timedelta_to_hours(
            timesheet_data.exclude(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
        )

        # Non-Billable: Approved hours where project_code == 'RB001'
        non_billable_hours = convert_timedelta_to_hours(
            timesheet_data.filter(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
        )
        utilization_percentage = round((total_worked_hours / budgeted_hours * 100) if budgeted_hours else 0, 2)

        
        task_data = []

        project_tasks = PhaseAllocation.objects.filter(project_code=project).select_related('task').distinct()

        for allocation in project_tasks:
            task = allocation.task

            task_worked_hours_td = timesheet_data.filter(task_description=task).aggregate(Sum('worked_hours'))['worked_hours__sum']
            task_worked_hours = convert_timedelta_to_hours(task_worked_hours_td) if task_worked_hours_td else 0

            # task_allocated_hours = convert_timedelta_to_hours(allocation.allocated_hours) if allocation.allocated_hours else 0
            if project.project_code == "RB001":
                task_allocated_hours = project.allocated_hours or 0
            else:
                task_allocated_hours = convert_timedelta_to_hours(allocation.allocated_hours) if allocation.allocated_hours else 0


            task_utilization = round((task_worked_hours / task_allocated_hours * 100), 2) if task_allocated_hours else 0

            task_data.append({
                "task_code": task.task_code,
                "task_group": task.task_group,
                "description": task.description,
                "budgeted_hours": allocation.budgeted_hours or 0,
                "allocated_hours": task_allocated_hours,
                "worked_hours": task_worked_hours,
                "phase_wise_utilization": task_utilization,
                "start_date": allocation.start_date,
                "end_date":allocation.end_date
            })

        # Now safe even if task_data is empty
        # total_allocated_hours = sum(task["allocated_hours"] for task in task_data)
        total_allocated_hours = project.allocated_hours or 0

        response_data.append({
            "project_code": project.project_code,
            "project_country": project.project_country,
            "project_region": project.project_region,
            "description": project.project_description,
            "project_type": project.project_type,
            "delivery_model": project.delivery_model,
            "start_date": project.from_date,
            "end_date": project.to_date,
            "project_status": project.project_status,
            "total_budgeted_hours": budgeted_hours,   
            "total_allocated_hours": total_allocated_hours,
            "total_worked_hours": total_worked_hours,
            "billable_hours": billable_hours,
            "non_billable_hours": non_billable_hours,
            "total_utilization": utilization_percentage,
            "task_description": task_data
        })

    return Response(response_data, status=status.HTTP_200_OK)


#get employee summary for multiple employees
@swagger_auto_schema(
    method='post',
    operation_description="Fetch employee summary details for multiple employees.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "employee_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="List of Employee Codes"
            )
        }
    ),
    responses={
        200: openapi.Response(
            "Employee summary retrieved successfully.",
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "employee_name": openapi.Schema(type=openapi.TYPE_STRING, description="Employee Name"),
                        "country": openapi.Schema(type=openapi.TYPE_STRING, description="Employee Country"),
                        "project_region": openapi.Schema(type=openapi.TYPE_STRING, description="Project Region"),
                        "project_country": openapi.Schema(type=openapi.TYPE_STRING, description="Project Country"),
                        "project_code": openapi.Schema(type=openapi.TYPE_STRING, description="Project Code"),
                        "description": openapi.Schema(type=openapi.TYPE_STRING, description="Project Description"),
                        "project_type": openapi.Schema(type=openapi.TYPE_STRING, description="Project Type"),
                        "delivery_model": openapi.Schema(type=openapi.TYPE_STRING, description="Delivery Model"),
                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project Start Date"),
                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project End Date"),
                        "project_status": openapi.Schema(type=openapi.TYPE_STRING, description="Project Status"),
                        "total_allocated_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Allocated Hours"),
                        "total_worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Worked Hours"),
                        "billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Billable Hours"),
                        "non_billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Non-Billable Hours"),
                        "utilization_percentage": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Utilization Percentage"),
                    }
                )
            )
        ),
        404: openapi.Response("Employees not found."),
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_summary(request):
    """Fetch employee summaries for multiple employees."""
    try:
        employee_codes = request.data.get("employee_code", [])

        if not employee_codes:
            return Response({"message": "No employee codes provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Get employees
        employees = Employee.objects.filter(employee_code__in=employee_codes)

        # Get project team entries (source of truth for assignments)
        project_teams = ProjectTeam.objects.filter(employee_code__in=employee_codes)

        # Get relevant projects
        project_codes = project_teams.values_list("project_code", flat=True).distinct()
        projects = Project.objects.filter(project_code__in=project_codes)

        # Get timesheets for all given employees (optional — may be empty)
        timesheets = EmployeeTimesheet.objects.filter(employee_code__in=employee_codes, status="approved")


        # Initialize response data
        response_data = []

        # for employee_code, employee in employees.items():
        for employee in employees:
            employee_code = employee.employee_code

            for project in projects:
                # Filter timesheet entries for the current employee and project
                project_timesheets = timesheets.filter(employee_code=employee_code, project_code=project.project_code)

                # Get task allocations for this employee and project
                employee_task_allocations = ProjectTeam.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code
                )

                # # Get ProjectTeam entry for dates
                # if project.project_code == "RB001":
                #     # Only one task, safe to get .first()
                #     team_entry = ProjectTeam.objects.filter(
                #         employee_code=employee_code,
                #         project_code=project.project_code
                #     ).first()

                #     team_start_date = team_entry.start_date if team_entry else project.from_date
                #     team_end_date = team_entry.end_date if team_entry else project.to_date
                # else:
                #     # Multiple tasks — get min and max
                #     date_range = ProjectTeam.objects.filter(
                #         employee_code=employee_code,
                #         project_code=project.project_code
                #     ).aggregate(
                #         min_start=models.Min("start_date"),
                #         max_end=models.Max("end_date")
                #     )
                #     team_start_date = date_range["min_start"] or project.from_date
                #     team_end_date = date_range["max_end"] or project.to_date
                # Default to project-level dates
                team_start_date = project.from_date
                team_end_date = project.to_date

                date_range = ProjectTeam.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code
                ).aggregate(
                    min_start=models.Min("start_date"),
                    max_end=models.Max("end_date")
                )

                # Only override if dates are within the project range
                if date_range["min_start"] and date_range["min_start"] >= project.from_date:
                    team_start_date = date_range["min_start"]

                if date_range["max_end"] and date_range["max_end"] <= project.to_date:
                    team_end_date = date_range["max_end"]


                # Sum allocated hours
                total_allocated_hours = convert_timedelta_to_hours(
                    employee_task_allocations.aggregate(Sum('allocated_hours'))['allocated_hours__sum']
                )

                # Compute total worked hours
                total_worked_hours = project_timesheets.aggregate(Sum('worked_hours'))['worked_hours__sum']
                total_worked_hours = convert_timedelta_to_hours(total_worked_hours)

                # Compute billable and non-billable hours
                billable_hours = convert_timedelta_to_hours(
                    project_timesheets.exclude(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
                )
                non_billable_hours = convert_timedelta_to_hours(
                    project_timesheets.filter(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
                )

                # Utilization %
                utilization_percentage = round((total_worked_hours / total_allocated_hours * 100) if total_allocated_hours else 0, 2)

                # Allocation till date
                till_allocated_hours = 0
                today = date.today()

                allocation_entries = ProjectTeamAllocation.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code
                )
                allocation_entry = ProjectTeamAllocation.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code
                ).first()

                allocation_percent = allocation_entry.allocation_percent if allocation_entry else 0


                if allocation_entries.exists():
                    for alloc in allocation_entries:
                        allocation_percent = alloc.allocation_percent or 0
                        alloc_start = team_start_date
                        alloc_end = min(today, team_end_date)

                        if alloc_start > alloc_end:
                            continue

                        working_days = get_working_days(alloc_start, alloc_end)
                        daily_hours = (allocation_percent / 100.0) * 8
                        till_allocated_hours += working_days * daily_hours
                else:
                    # Assume 100% allocation if no record
                    alloc_start = team_start_date
                    alloc_end = min(today, team_end_date)

                    if alloc_start <= alloc_end:
                        working_days = get_working_days(alloc_start, alloc_end)
                        till_allocated_hours = working_days * 8

                till_allocated_hours = round(till_allocated_hours, 2)
                till_utilization = round((total_worked_hours / till_allocated_hours * 100) if till_allocated_hours else 0, 2)

                response_data.append({
                    "employee_name": employee.name,
                    "country": employee.country,
                    "project_region": project.project_region,
                    "project_country": project.project_country,
                    "project_code": project.project_code,
                    "description": project.project_description,
                    "project_type": project.project_type,
                    "delivery_model": project.delivery_model,
                    "start_date": team_start_date,
                    "end_date": team_end_date,
                    "project_status": project.project_status,
                    "total_allocated_hours": total_allocated_hours,
                    "total_worked_hours": total_worked_hours,
                    "billable_hours": billable_hours,
                    "non_billable_hours": non_billable_hours,
                    "utilization_percentage": utilization_percentage,
                    "till_allocated_hours": till_allocated_hours,
                    "till_utilization": till_utilization,
                    "allocation_percent": allocation_percent,
                })

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#get employee summary detailed by tasks
@swagger_auto_schema(
    method='post',
    operation_description="Fetch employee detailed summary by tasks using a list of employee_code values.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "employee_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="List of Employee Codes"
            )
        },
        required=["employee_code"]
    ),
    responses={
        200: openapi.Response(
            "Employee detailed summary retrieved successfully.",
            openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "employee_name": openapi.Schema(type=openapi.TYPE_STRING, description="Employee Name"),
                        "country": openapi.Schema(type=openapi.TYPE_STRING, description="Employee Country"),
                        "project_region": openapi.Schema(type=openapi.TYPE_STRING, description="Project Region"),
                        "project_country": openapi.Schema(type=openapi.TYPE_STRING, description="Project Country"),
                        "project_code": openapi.Schema(type=openapi.TYPE_STRING, description="Project Code"),
                        "description": openapi.Schema(type=openapi.TYPE_STRING, description="Project Description"),
                        "project_type": openapi.Schema(type=openapi.TYPE_STRING, description="Project Type"),
                        "delivery_model": openapi.Schema(type=openapi.TYPE_STRING, description="Delivery Model"),
                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project Start Date"),
                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project End Date"),
                        "project_status": openapi.Schema(type=openapi.TYPE_STRING, description="Project Status"),
                        "task_description": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "task_code": openapi.Schema(type=openapi.TYPE_STRING, description="Task Code"),
                                    "task_group": openapi.Schema(type=openapi.TYPE_STRING, description="Task Group"),
                                    "description": openapi.Schema(type=openapi.TYPE_STRING, description="Task Description"),
                                    "billable": openapi.Schema(type=openapi.TYPE_STRING, description="Billable Status"),
                                    "allocated_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Allocated Hours"),
                                    "worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Worked Hours"),
                                }
                            )
                        ),
                        "total_allocated_hours": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total Allocated Hours"),
                        "total_worked_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Worked Hours"),
                        "billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Billable Hours"),
                        "non_billable_hours": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Total Non-Billable Hours"),
                        "utilization_percentage": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Utilization Percentage"),
                    }
                )
            )
        ),
        404: openapi.Response("Employee not found."),
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_detailed_summary(request):
    try:
        employee_codes = request.data.get("employee_code", [])

        if not employee_codes or not isinstance(employee_codes, list):
            return Response({"message": "Invalid or missing employee_code list."}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []

        for employee_code in employee_codes:
            #  Get employee object
            employee_obj = Employee.objects.filter(employee_code=employee_code).first()
            if not employee_obj:
                continue

            #  Get projects from assignments (ProjectTeam) and timesheets
            team_projects = ProjectTeam.objects.filter(employee_code=employee_code).values_list("project_code", flat=True)
            timesheet_projects = EmployeeTimesheet.objects.filter(employee_code=employee_code).values_list("project_code", flat=True)

            combined_project_codes = set(team_projects).union(set(timesheet_projects))
            projects = Project.objects.filter(project_code__in=combined_project_codes)

            for project in projects:
                #  Get all tasks from team assignment and timesheet
                team_tasks = ProjectTeam.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code
                ).values_list("task", flat=True)

                timesheet_tasks = EmployeeTimesheet.objects.filter(
                    employee_code=employee_code,
                    project_code=project.project_code,
                    status='approved'
                ).values_list("task_description", flat=True)

                combined_task_codes = set(team_tasks).union(set(timesheet_tasks))

                task_data = []
                total_allocated_hours = 0
                total_worked_hours = 0
                billable_hours = 0
                non_billable_hours = 0

                for task_code in combined_task_codes:
                    task_obj = ProjectTasks.objects.filter(task_code=task_code).first()
                    if not task_obj:
                        continue

                    #  Get timesheets for this task
                    task_timesheets = EmployeeTimesheet.objects.filter(
                        employee_code=employee_code,
                        project_code=project.project_code,
                        task_description=task_code,
                        status='approved'
                    )

                    task_worked_hours = convert_timedelta_to_hours(
                        task_timesheets.aggregate(Sum('worked_hours'))['worked_hours__sum']
                    )

                    #  Allocation from ProjectTeam
                    task_allocated_hours = ProjectTeam.objects.filter(
                        employee_code=employee_code,
                        project_code=project.project_code,
                        task=task_obj
                    ).aggregate(total=Sum("allocated_hours"))["total"] or 0

                    total_allocated_hours += task_allocated_hours
                    total_worked_hours += task_worked_hours

                    #  Billable / Non-billable logic
                    for entry in task_timesheets:
                        worked = convert_timedelta_to_hours(entry.worked_hours)
                        if entry.project_code.project_code == "RB001":
                            non_billable_hours += worked
                        else:
                            billable_hours += worked

                    utilization = round((task_worked_hours / task_allocated_hours * 100), 2) if task_allocated_hours else 0

                    #  Dates and allocation percent
                    task_team_entry = ProjectTeam.objects.filter(
                        employee_code=employee_code,
                        project_code=project.project_code,
                        task=task_obj
                    ).first()

                    allocation_entry = ProjectTeamAllocation.objects.filter(
                        employee_code=employee_code,
                        project_code=project.project_code
                    ).first()

                    till_allocated_hours = 0
                    task_start = task_end = None
                    allocation_percent = 0

                    if task_team_entry:
                        task_start = task_team_entry.start_date
                        task_end = task_team_entry.end_date
                        if task_start and task_end:
                            cutoff_date = min(task_end, date.today())
                            working_days = get_working_days(task_start, cutoff_date)

                            allocation_percent = allocation_entry.allocation_percent if allocation_entry else 100
                            daily_hours = (allocation_percent / 100.0) * 8
                            till_allocated_hours = round(working_days * daily_hours, 2)

                    till_utilization = round((task_worked_hours / till_allocated_hours * 100), 2) if till_allocated_hours else 0

                    task_data.append({
                        "task_code": task_code,
                        "task_group": task_obj.task_group,
                        "description": task_obj.description,
                        "allocated_hours": task_allocated_hours,
                        "worked_hours": task_worked_hours,
                        "phase_wise_utilization": utilization,
                        "start_date": task_start,
                        "end_date": task_end,
                        "till_allocated_hours": till_allocated_hours,
                        "till_utilization": till_utilization
                    })

                overall_utilization = round((total_worked_hours / total_allocated_hours * 100), 2) if total_allocated_hours else 0

                response_data.append({
                    "employee_name": employee_obj.name,
                    "country": employee_obj.country,
                    "project_region": project.project_region,
                    "project_country": project.project_country,
                    "project_code": project.project_code,
                    "description": project.project_description,
                    "project_type": project.project_type,
                    "delivery_model": project.delivery_model,
                    "start_date": project.from_date,
                    "end_date": project.to_date,
                    "project_status": project.project_status,
                    "task_description": task_data,
                    "total_allocated_hours": total_allocated_hours,
                    "total_worked_hours": total_worked_hours,
                    "billable_hours": billable_hours,
                    "non_billable_hours": non_billable_hours,
                    "total_utilization": overall_utilization,
                })

        if not response_data:
            return Response({"message": "No data found for the given employee codes."}, status=status.HTTP_404_NOT_FOUND)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#get project hours 
@swagger_auto_schema(
    method="post",
    operation_description="Retrieve project hours based on project code.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_code": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Project code to retrieve employee project hours"
            )
        },
        required=["project_code"],
    ),
    responses={
        200: openapi.Response("Project hours retrieved successfully."),
        400: "Bad Request - Validation error.",
    },
)
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_hours_by_project(request):
    try:
        project_code = request.data.get("project_code")

        if not project_code:
            return Response({"error": "project_code is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch project details
        project = Project.objects.filter(project_code=project_code).first()
        if not project:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        project_name = project.project_description  # Assuming this field exists

        # Fetch employees assigned to this project
        project_employees = ProjectTeam.objects.filter(project_code=project_code).select_related("employee_code", "task")

        if not project_employees.exists():
            return Response({"message": "No employees allocated to this project"}, status=status.HTTP_200_OK)

        phase_dict = {}

        for assignment in project_employees:
            phase_name = assignment.task.task_group  # Assuming `task` has `task_group`
            allocated_hours = assignment.allocated_hours
            #  Fetch budgeted hours from PhaseAllocation table
            phase_alloc = PhaseAllocation.objects.filter(project_code=assignment.project_code, task=assignment.task).first()
            budgeted_hours = phase_alloc.budgeted_hours if phase_alloc else 0  # Default to 0 if not found

            # Fetch timesheet data for this employee and project phase
            timesheets = EmployeeTimesheet.objects.filter(
                employee_code=assignment.employee_code,
                project_code=assignment.project_code,
                task_description=assignment.task,
                status="approved"  # Only include approved hours
            )
            # Convert timedelta to "HH:MM" format
            def format_timedelta(td):
                """Converts timedelta to HH:MM formatted string."""
                total_seconds = int(td.total_seconds())  # Get total seconds
                hours, minutes = divmod(total_seconds // 60, 60)  # Convert to HH:MM
                return f"{hours:02d}:{minutes:02d}"  # Return formatted string
            # Calculate total worked hours from all timesheets for this employee & project phase
            total_worked_seconds = sum(ts.worked_hours.total_seconds() for ts in timesheets if ts.worked_hours)
            total_worked_hours = format_timedelta(timedelta(seconds=total_worked_seconds))  # Convert to HH:MM
            worked_hours_in_hours = total_worked_seconds / 3600  # Convert to hours for balance calculation

            # Balance hours calculation
            balance_hours = allocated_hours - worked_hours_in_hours

            # Group by phase
            if phase_name not in phase_dict:
                phase_dict[phase_name] = {
                    "phase_name": phase_name,
                    "budgeted_hours": budgeted_hours,  # Assuming budgeted hours exist per project
                    "allocated_hours": 0,
                    "worked_hours": "00:00",
                    "balance_hours": 0
                }

            phase_dict[phase_name]["allocated_hours"] += allocated_hours
            phase_dict[phase_name]["balance_hours"] = round(phase_dict[phase_name]["balance_hours"] + balance_hours, 2)

            # Convert worked hours correctly
            current_worked_hours = phase_dict[phase_name]["worked_hours"]
            new_worked_hours = total_worked_hours  # The new worked hours from timesheet

            # Convert both to total minutes
            try:
                current_hours, current_mins = map(int, current_worked_hours.split(":"))
                new_hours, new_mins = map(int, new_worked_hours.split(":"))

                # Convert both to total minutes
                current_total_minutes = (current_hours * 60) + current_mins
                new_total_minutes = (new_hours * 60) + new_mins

                # Sum up the minutes
                total_minutes = current_total_minutes + new_total_minutes

                # Convert back to HH:MM format
                updated_hours = total_minutes // 60
                updated_mins = total_minutes % 60

                # phase_dict[phase_name]["worked_hours"] = f"{updated_hours}:{updated_mins:02d}"
                phase_dict[phase_name]["worked_hours"] = f"{updated_hours:02d}:{updated_mins:02d}"

            except Exception as e:
                return Response({"error": f"Worked hours format issue: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Convert dict to list
        response_data = {
            "project_code": project.project_code,
            "project_name": project_name,
            "phases": list(phase_dict.values()),
        }

        return Response({"message": "Project hours retrieved successfully", "data": response_data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def update_phase_allocation_worked_hours(project_code, task_code):

    # print(f" Trying to update worked_hours for project={project_code} | task_code={task_code}")

    phase = PhaseAllocation.objects.filter(
        project_code=project_code,
        task__task_code=task_code
    ).first()

    if not phase:
        # print(f" No PhaseAllocation found for project={project_code} and task_code={task_code}")
        return

    # Calculate total worked hours
    total_time = EmployeeTimesheet.objects.filter(
        project_code=project_code,
        task_description=task_code,  # if task_code is used in timesheet
        status="approved"
    ).aggregate(total=Sum("worked_hours"))["total"]

    if total_time:
        if isinstance(total_time, timedelta):
            total_seconds = int(total_time.total_seconds())
        else:
            total_seconds = int(total_time * 3600)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        worked_str = f"{hours}:{minutes:02}"
    else:
        worked_str = "00:00"

    if phase.worked_hours != worked_str:
        phase.worked_hours = worked_str
        phase.save(update_fields=["worked_hours"])
        print(f" Updated worked_hours = {worked_str} for PhaseAllocation ID {phase.id}")
    else:
        print(" worked_hours already up-to-date.")



def working_days_between(start_date, end_date):
    """Return count of weekdays (Mon–Fri) between two dates."""
    days = np.busday_count(start_date, (end_date + timedelta(days=1)))
    return int(days)


def convert_to_decimal_hours(time_value):
    if not time_value:
        return 0
    return time_value.total_seconds() / 3600


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            ),
            "period_type": openapi.Schema(type=openapi.TYPE_STRING, enum=["date_range", "month_year"]),
            "from_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            "to_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            "month": openapi.Schema(type=openapi.TYPE_INTEGER),
            "year": openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=["project_code", "period_type"]
    ),
    operation_description="Fetch project summary within a date range or month-year period.",
)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_summary_periodwise(request):
    try:
        data = request.data
        project_codes = data.get("project_code", [])
        period_type = data.get("period_type")

        if not project_codes or not isinstance(project_codes, list):
            return Response({"message": "Provide valid project_code list."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Determine period range ---
        from_date = None
        to_date = None

        if period_type == "date_range":
            from_date_str = data.get("from_date")
            to_date_str = data.get("to_date")

            if (not from_date_str or not to_date_str) and data.get("month") and data.get("year"):
                period_type = "month_year"
            elif not from_date_str or not to_date_str:
                return Response(
                    {"message": "from_date and to_date required for date_range."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()

        if period_type == "month_year":
            month = data.get("month")
            year = data.get("year")
            if not (month and year):
                return Response(
                    {"message": "month and year required for month_year."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            from_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            to_date = date(year, month, last_day)

        # --- Fetch projects ---
        projects = Project.objects.filter(project_code__in=project_codes)
        if not projects.exists():
            return Response({"message": "No projects found."}, status=status.HTTP_404_NOT_FOUND)

        # --- Validate project active period ---
        invalid_projects = []
        for project in projects:
            project_start = project.from_date
            project_end = project.to_date

            if not project_start or not project_end:
                continue

            if from_date < project_start or to_date > project_end:
                invalid_projects.append(
                    f"Project {project.project_code} is active only between "
                    f"{project_start.strftime('%Y-%m-%d')} and {project_end.strftime('%Y-%m-%d')}. "
                    f"Please select a date range within this period."
                )

        if invalid_projects:
            # You can return all messages as a list if needed
            return Response({"message": invalid_projects[0]}, status=status.HTTP_400_BAD_REQUEST)

        # --- Only include projects active within the requested period ---
        filtered_projects = projects.filter(from_date__lte=to_date, to_date__gte=from_date)

        response_data = []

        for project in filtered_projects:
            timesheet_data = EmployeeTimesheet.objects.filter(
                project_code=project.project_code,
                status="approved",
                date__range=(from_date, to_date)
            )

            total_worked_hours_periodwise = sum(
                convert_to_decimal_hours(entry.worked_hours) for entry in timesheet_data
            )

            total_allocated_hours_periodwise = working_days_between(from_date, to_date) * 8

            utilization_periodwise = round(
                (total_worked_hours_periodwise / total_allocated_hours_periodwise * 100)
                if total_allocated_hours_periodwise else 0, 2
            )
            month_year_label = ""
            if period_type == "month_year":
                month_year_label = f"{calendar.month_abbr[month]}'{str(year)[-2:]}"

            response_data.append({
                "project_code": project.project_code,
                "project_country": getattr(project, "project_country", None),
                "project_region": getattr(project, "project_region", None),
                "description": getattr(project, "project_description", None),
                "project_type": getattr(project, "project_type", None),
                "delivery_model": getattr(project, "delivery_model", None),
                "start_date": project.from_date.strftime("%Y-%m-%d") if project.from_date else None,
                "end_date": project.to_date.strftime("%Y-%m-%d") if project.to_date else None,
                "project_status": project.project_status,
                "total_budgeted_hours": getattr(project, "allocated_budgeted_hours", 0),
                "total_allocated_hours": getattr(project, "allocated_hours", 0),
                "total_worked_hours": getattr(project, "worked_hours", 0),
                "billable_hours": getattr(project, "billable_hours", 0),
                "non_billable_hours": getattr(project, "non_billable_hours", 0),
                "utilization_percentage": getattr(project, "utilization_percentage", 0),
                "total_allocated_hours_periodwise": total_allocated_hours_periodwise,
                "total_worked_hours_periodwise": round(total_worked_hours_periodwise, 2),
                "utilization_periodwise": utilization_periodwise,
                "month_year": month_year_label,
            })

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
@swagger_auto_schema(
    method='post',
    operation_description="Fetch project detailed summary (task-wise) within a date range or month-year period.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_code": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING)
            ),
            "period_type": openapi.Schema(type=openapi.TYPE_STRING, enum=["date_range", "month_year"]),
            "from_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            "to_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            "month": openapi.Schema(type=openapi.TYPE_INTEGER),
            "year": openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=["project_code", "period_type"]
    ),
    responses={
        200: openapi.Response("Project detailed periodwise summary retrieved successfully."),
        400: openapi.Response("Invalid request body."),
        404: openapi.Response("Projects not found."),
    },
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_detailed_periodwise(request):
    try:
        data = request.data
        project_codes = data.get("project_code", [])
        period_type = data.get("period_type")

        if not project_codes or not isinstance(project_codes, list):
            return Response({"message": "Provide valid project_code list."}, status=status.HTTP_400_BAD_REQUEST)

        from_date = None
        to_date = None
        month_year_label = ""  
        # --- Handle period type ---
        if period_type == "date_range":
            from_date_str = data.get("from_date")
            to_date_str = data.get("to_date")

            if (not from_date_str or not to_date_str) and data.get("month") and data.get("year"):
                period_type = "month_year"
            elif not from_date_str or not to_date_str:
                return Response({"message": "from_date and to_date required for date_range."},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()

        if period_type == "month_year":
            month = data.get("month")
            year = data.get("year")
            if not (month and year):
                return Response({"message": "month and year required for month_year."},
                                status=status.HTTP_400_BAD_REQUEST)
            from_date = date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            to_date = date(year, month, last_day)
            month_year_label = f"{calendar.month_abbr[month]}'{str(year)[-2:]}"  

        # --- Fetch and validate projects ---
        projects = Project.objects.filter(project_code__in=project_codes)
        if not projects.exists():
            return Response({"message": "No projects found."}, status=status.HTTP_404_NOT_FOUND)

        for project in projects:
            project_start = project.from_date
            project_end = project.to_date
            if from_date < project_start or to_date > project_end:
                return Response({
                    "message": (
                        f"Project {project.project_code} is active only between "
                        f"{project_start.strftime('%Y-%m-%d')} and {project_end.strftime('%Y-%m-%d')}. "
                        f"Please select a date range within this period."
                    )
                }, status=status.HTTP_400_BAD_REQUEST)

        filtered_projects = projects.filter(from_date__lte=to_date, to_date__gte=from_date)
        response_data = []

        # --- Project-wise loop ---
        for project in filtered_projects:
            project_phases = PhaseAllocation.objects.filter(project_code=project)
            if not project_phases.exists():
                continue  

            phase_start_date = project_phases.aggregate(Min("start_date"))["start_date__min"]
            phase_end_date = project_phases.aggregate(Max("end_date"))["end_date__max"]

            effective_from_date = max(from_date, phase_start_date) if phase_start_date else from_date
            effective_to_date = min(to_date, phase_end_date) if phase_end_date else to_date

            timesheet_data = EmployeeTimesheet.objects.filter(
                project_code=project.project_code,
                status='approved',
                date__range=(effective_from_date, effective_to_date)
            )

            total_allocated_hours = convert_timedelta_to_hours(project.allocated_hours)
            budgeted_hours = convert_timedelta_to_hours(project.budgeted_hours)
            total_worked_hours = convert_timedelta_to_hours(
                timesheet_data.aggregate(Sum('worked_hours'))['worked_hours__sum']
            )

            billable_hours = convert_timedelta_to_hours(
                timesheet_data.exclude(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
            )
            non_billable_hours = convert_timedelta_to_hours(
                timesheet_data.filter(project_code="RB001").aggregate(Sum('worked_hours'))['worked_hours__sum']
            )

            utilization_percentage = round(
                (total_worked_hours / budgeted_hours * 100) if budgeted_hours else 0, 2
            )

            task_data = []
            project_tasks = project_phases.select_related('task').distinct()

            for allocation in project_tasks:
                task = allocation.task
                effective_task_start = max(allocation.start_date, from_date)
                effective_task_end = min(allocation.end_date, to_date)

                if effective_task_start > effective_task_end:
                    phase_allocated_hours_periodwise = 0
                    phase_worked_hours_periodwise = 0
                    phase_utilization_periodwise = 0
                else:
                    overlapping_days = working_days_between(effective_task_start, effective_task_end)
                    phase_allocated_hours_periodwise = overlapping_days * 8

                    phase_worked_hours_td = timesheet_data.filter(
                        task_description=task,
                        date__range=(effective_task_start, effective_task_end)
                    ).aggregate(Sum("worked_hours"))["worked_hours__sum"]

                    phase_worked_hours_periodwise = convert_timedelta_to_hours(phase_worked_hours_td) if phase_worked_hours_td else 0
                    phase_utilization_periodwise = round(
                        (phase_worked_hours_periodwise / phase_allocated_hours_periodwise * 100)
                        if phase_allocated_hours_periodwise else 0,
                        2,
                    )

                task_worked_hours_td = timesheet_data.filter(task_description=task).aggregate(Sum('worked_hours'))['worked_hours__sum']
                task_worked_hours = convert_timedelta_to_hours(task_worked_hours_td) if task_worked_hours_td else 0

                if project.project_code == "RB001":
                    task_allocated_hours = convert_timedelta_to_hours(project.allocated_hours)
                else:
                    task_allocated_hours = convert_timedelta_to_hours(allocation.allocated_hours) if allocation.allocated_hours else 0

                task_utilization = round(
                    (task_worked_hours / task_allocated_hours * 100), 2
                ) if task_allocated_hours else 0

                task_data.append({
                    "task_code": task.task_code,
                    "task_group": task.task_group,
                    "description": task.description,
                    "budgeted_hours": allocation.budgeted_hours or 0,
                    "allocated_hours": task_allocated_hours,
                    "worked_hours": task_worked_hours,
                    "phase_wise_utilization": task_utilization,
                    "start_date": allocation.start_date,
                    "end_date": allocation.end_date,
                    "total_allocated_hours_periodwise": phase_allocated_hours_periodwise,
                    "total_worked_hours_periodwise": phase_worked_hours_periodwise,
                    "utilization_periodwise": phase_utilization_periodwise,
                })

           
            response_data.append({
                "project_code": project.project_code,
                "project_country": project.project_country,
                "project_region": project.project_region,
                "description": project.project_description,
                "project_type": project.project_type,
                "delivery_model": project.delivery_model,
                "start_date": effective_from_date,
                "end_date": effective_to_date,
                "project_status": project.project_status,
                "total_budgeted_hours": budgeted_hours,
                "total_allocated_hours": total_allocated_hours,
                "total_worked_hours": total_worked_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": non_billable_hours,
                "total_utilization": utilization_percentage,
                "month_year": month_year_label, 
                "task_description": task_data,
            })

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
