
from rest_framework.decorators import api_view
from django.db.models import Sum,Q
from rest_framework.response import Response
from django.utils import timezone
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import EmployeeTimesheet
from pmo.models import ProjectTeam,PhaseAllocation,Project,ProjectTeamAllocation,ProjectTeamAllocationHistory,PhaseTeamAllocation,PhaseTeamAllocationHistory
from .serializers import EmployeeTimesheetSerializer
from django.db.models import Sum, DurationField
from django.db.models.functions import Cast
from master_data.models import Employee, ProjectTasks
from user_management.models import UserProfile
from datetime import timedelta,datetime
import json
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import escape
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from datetime import date



def convert_time_to_minutes(time_str):
    """Convert 'HH:MM' format to total minutes (integer)."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except ValueError:
        raise ValueError("Invalid time format. Use 'HH:MM'.")
    
#add timesheet   
# @swagger_auto_schema(
#     method="post",
#     operation_description="Add one or more timesheet entries.",
#     request_body=EmployeeTimesheetSerializer(many=True),
#     responses={
#         201: openapi.Response("Timesheet entry(s) created successfully.", EmployeeTimesheetSerializer(many=True)),
#         400: "Bad Request - Validation error.",
#     },
# )
# @api_view(["POST"])
# def add_timesheet(request):
#     try:
#         if not isinstance(request.data, list):  # Ensure request body is a list
#             return Response({"error": "Expected a list of timesheets"}, status=status.HTTP_400_BAD_REQUEST)

#         #  Pass `context={"request": request}`
#         serializer = EmployeeTimesheetSerializer(data=request.data, many=True, context={"request": request})

#         if serializer.is_valid():
#             saved_records = serializer.save()
#             response_data = EmployeeTimesheetSerializer(saved_records, many=True).data
#             return Response({"message": "Timesheet added successfully", "data": response_data}, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON format"}, status=400)

#add timesheet

def get_phase_allocation_percent_for_date(employee, project, task, entry_date):
    """
    Returns (allocation_percent, alloc_start, alloc_end) for the given date.
    Fetches from PhaseTeamAllocationHistory and falls back to PhaseTeamAllocation.
    """
    from datetime import date

    history_qs = PhaseTeamAllocationHistory.objects.filter(
        allocation__employee=employee,
        allocation__project=project,
        allocation__task=task,
        allocation_start_date__lte=entry_date,
        allocation_end_date__gte=entry_date
    ).order_by('-updated_at')

    if history_qs.exists():
        h = history_qs.first()
        return h.allocation_percent, h.allocation_start_date, h.allocation_end_date

    alloc = PhaseTeamAllocation.objects.filter(
        employee=employee,
        project=project,
        task=task
    ).first()

    if alloc:
        return alloc.allocation_percent, alloc.allocation_start_date, alloc.allocation_end_date

    return None, None, None



@swagger_auto_schema(
    method="post",
    operation_description="Add one or more timesheet entries.",
    request_body=EmployeeTimesheetSerializer(many=True),
    responses={
        201: openapi.Response("Timesheet entry(s) created successfully.", EmployeeTimesheetSerializer(many=True)),
        400: "Bad Request - Validation error.",
    },
)
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_timesheet(request):
    try:
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of timesheets"}, status=400)

        timesheet_entries = request.data
        validated_entries = []
        entry_group = {}

        for entry in timesheet_entries:
            employee_code = entry.get("employee_code")
            project_code = entry.get("project_code")
            task_code = entry.get("task_description")
            worked_hours_str = entry.get("worked_hours")
            entry_date = entry.get("date")

            if not all([employee_code, project_code, task_code, worked_hours_str, entry_date]):
                return Response({"error": f"Missing fields in entry: {entry}"}, status=400)

            # Convert worked_hours string to timedelta
            try:
                worked_hours = datetime.strptime(worked_hours_str, "%H:%M") - datetime.strptime("00:00", "%H:%M")
            except ValueError:
                return Response({"error": f"Invalid time format in worked_hours: {worked_hours_str}. Use HH:MM"}, status=400)

            # Convert entry_date string to date object
            try:
                entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": f"Invalid date format in 'date': {entry_date}. Use YYYY-MM-DD"}, status=400)

            try:
                employee = Employee.objects.get(employee_code=employee_code)
                project = Project.objects.get(project_code=project_code)
                task = ProjectTasks.objects.get(task_code=task_code)
                # Block timesheets on or after relieving date
                if employee.relieving_date and entry_date_obj >= employee.relieving_date:
                    return Response({
                        "error": f"Cannot add timesheet for {entry_date_obj}. Employee '{employee_code}' relieved on {employee.relieving_date}."
                    }, status=400)

                team_qs = ProjectTeam.objects.filter(employee_code=employee, project_code=project)

                if not team_qs.exists():
                    return Response({"error": f"Project {project_code} not assigned to employee {employee_code}."}, status=400)

                team = team_qs.filter(start_date__lte=entry_date_obj, end_date__gte=entry_date_obj).first()
                if not team:
                    team = team_qs.order_by('-end_date').first()

                proj_start = team.start_date
                proj_end = team.end_date or proj_start

                if entry_date_obj < proj_start or entry_date_obj > proj_end:
                    return Response({
                        "error": f"Timesheet date {entry_date_obj} is outside your assignment on project {project_code} ({proj_start} to {proj_end})."
                    }, status=400)

                leave_duration = get_allowed_leave_duration(entry.get("new_description"))

                # RB001 has no allocation restriction
                if project_code == "RB001":
                    allowed_duration = None
                elif leave_duration:
                    allowed_duration = leave_duration
                else:
                    allocation_percent, alloc_start, alloc_end = get_phase_allocation_percent_for_date(
                        employee, project, task, entry_date_obj
                    )  

                    if allocation_percent is None:
                        alloc_record = PhaseTeamAllocation.objects.filter(
                            employee=employee, project=project, task=task
                        ).first()
                        phase_name = task.task_group 
                        if alloc_record:
                            return Response({
                                "error": (
                                    f"Allocation dates for phase '{phase_name}' must be within project duration: "
                                    f"{alloc_record.allocation_start_date} to {alloc_record.allocation_end_date}. "
                                    f"Received: {entry_date_obj}"
                                )
                            }, status=400)
                        else:
                            return Response({
                                "error": f"No allocation found in phase '{phase_name}' on {entry_date_obj}."
                            }, status=400)


                    if alloc_start and alloc_end and (entry_date_obj < alloc_start or entry_date_obj > alloc_end):
                        return Response({"error": f"Allocation % not found for date: {entry_date_obj}"}, status=400)

                    if allocation_percent == 0:
                        return Response({
                            "error": f"Timesheet not allowed. Allocation percentage is 0% for {employee_code} in {project_code}, task {task_code} on {entry_date_obj}."
                        }, status=400)

                    if allocation_percent > 100:
                        return Response({
                            "error": f"Invalid allocation percent ({allocation_percent}%) for {employee_code} in {project_code}, task {task_code}."
                        }, status=400)

                    allowed_hours = min((allocation_percent / 100) * 8, 8)
                    allowed_duration = timedelta(hours=allowed_hours)

            except (Employee.DoesNotExist, Project.DoesNotExist, ProjectTasks.DoesNotExist):
                return Response({"error": f"Invalid employee/project/task in entry: {entry}"}, status=400)

            # <-- UPDATED KEY
            key = (employee_code, project_code, task_code, entry_date)

            existing_total = sum((ts.worked_hours for ts in EmployeeTimesheet.objects.filter(
                employee_code=employee_code,
                project_code=project_code,
                task_description_id=task_code,
                date=entry_date
            ).exclude(status__iexact="rejected")), timedelta())

            # Add current request
            if key not in entry_group:
                entry_group[key] = worked_hours
            else:
                entry_group[key] += worked_hours

            cumulative_hours = existing_total + entry_group[key]

            if allowed_duration and cumulative_hours > allowed_duration:
                return Response({
                    "error": (
                        f"Worked hours exceeded in project {project_code} on {entry_date}. "
                        f"Allowed: {allowed_duration}, "
                        f"Attempting to add: {entry_group[key]}, Total: {cumulative_hours}"
                    )
                }, status=400)

            entry["worked_hours"] = str(worked_hours)
            validated_entries.append(entry)

        serializer = EmployeeTimesheetSerializer(data=validated_entries, many=True, context={"request": request})
        if serializer.is_valid():
            saved_records = serializer.save()
            return Response({"message": "Timesheet added successfully", "data": serializer.data}, status=201)

        return Response(serializer.errors, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

def get_allowed_leave_duration(new_description):
    """
    Determine allowed worked hours based on the leave type description.
    Returns timedelta of allowed hours or None if not a special leave.
    """
    if not new_description:
        return None

    desc = new_description.lower()

    if "half day leave" in desc:
        return timedelta(hours=4)
    elif any(keyword in desc for keyword in ["sick leave", "full day leave", "client holiday / designated holiday"]):
        return timedelta(hours=8)

    return None

#edit timesheet
@swagger_auto_schema(
    method="put",
    operation_description="Edit one or more timesheet entries.",
    request_body=EmployeeTimesheetSerializer(many=True),
    responses={
        200: openapi.Response("Timesheet entry(s) updated successfully.", EmployeeTimesheetSerializer(many=True)),
        400: "Bad Request - Validation error.",
        404: "Not Found - Timesheet entry does not exist.",
    },
)
@api_view(["PUT"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_timesheet(request):
    try:
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of timesheets"}, status=400)

        updated_entries = []
        entry_group = {}  # (employee, project, task, date) cumulative for current request

        for entry in request.data:
            entry_id = entry.get("id")
            if not entry_id:
                return Response({"error": "Each entry must include an 'id' to update."}, status=400)

            try:
                timesheet_instance = EmployeeTimesheet.objects.get(id=entry_id)
            except EmployeeTimesheet.DoesNotExist:
                return Response({"error": f"Timesheet with id {entry_id} not found."}, status=404)

            # Extract new values
            employee_code = entry.get("employee_code")
            project_code = entry.get("project_code")
            task_code = entry.get("task_description")
            worked_hours_str = entry.get("worked_hours")
            entry_date_str = entry.get("date")

            if not all([employee_code, project_code, task_code, worked_hours_str, entry_date_str]):
                return Response({"error": f"Missing fields in entry: {entry}"}, status=400)

            # Parse worked hours
            try:
                worked_hours = datetime.strptime(worked_hours_str, "%H:%M") - datetime.strptime("00:00", "%H:%M")
            except ValueError:
                return Response({"error": f"Invalid time format in worked_hours: {worked_hours_str}. Use HH:MM"}, status=400)

            # Parse date
            try:
                entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": f"Invalid date: {entry_date_str}. Use YYYY-MM-DD"}, status=400)

            # Validate employee, project, task
            try:
                employee = Employee.objects.get(employee_code=employee_code)
                project = Project.objects.get(project_code=project_code)
                task = ProjectTasks.objects.get(task_code=task_code)
            except:
                return Response({"error": f"Invalid employee/project/task in entry: {entry}"}, status=400)

            # Block after relieving date
            if employee.relieving_date and entry_date >= employee.relieving_date:
                return Response({
                    "error": f"Cannot edit timesheet for {entry_date}. Employee '{employee_code}' relieved on {employee.relieving_date}."
                }, status=400)

            # Validate project assignment
            team_qs = ProjectTeam.objects.filter(employee_code=employee, project_code=project)
            if not team_qs.exists():
                return Response({"error": f"Project {project_code} not assigned to employee {employee_code}."}, status=400)

            team = team_qs.filter(start_date__lte=entry_date, end_date__gte=entry_date).first()
            if not team:
                team = team_qs.order_by('-end_date').first()

            proj_start = team.start_date
            proj_end = team.end_date or proj_start

            if entry_date < proj_start or entry_date > proj_end:
                return Response({
                    "error": f"Timesheet date {entry_date} is outside your assignment on project {project_code} ({proj_start} to {proj_end})."
                }, status=400)

            # Leave rule check
            leave_duration = get_allowed_leave_duration(entry.get("new_description"))

            # Allocation logic
            if project_code == "RB001":
                allowed_duration = None  # unrestricted
            elif leave_duration:
                allowed_duration = leave_duration
            else:
                allocation_percent, alloc_start, alloc_end = get_phase_allocation_percent_for_date(
                        employee, project, task, entry_date
                )

                if allocation_percent is None:
                    alloc_record = PhaseTeamAllocation.objects.filter(
                        employee=employee, project=project, task=task
                    ).first()
                    phase_name = task.task_group  # Get the phase name for better message

                    if alloc_record:
                        return Response({
                            "error": (
                                f"Allocation dates for phase '{phase_name}' must be within project duration: "
                                f"{alloc_record.allocation_start_date} to {alloc_record.allocation_end_date}. "
                                f"Received: {entry_date}"
                            )
                        }, status=400)
                    else:
                        return Response({
                            "error": f"No allocation found in phase '{phase_name}' on {entry_date}."
                        }, status=400)


                if alloc_start and alloc_end and (entry_date < alloc_start or entry_date > alloc_end):
                    return Response({"error": f"Allocation % not found for date: {entry_date}"}, status=400)

                if allocation_percent == 0:
                    return Response({
                        "error": f"Timesheet not allowed. Allocation percent is 0% for {employee_code} in {project_code}, task {task_code} on {entry_date}."
                    }, status=400)

                if allocation_percent > 100:
                    return Response({
                        "error": f"Invalid allocation percent ({allocation_percent}%) for {employee_code} in {project_code}, task {task_code}."
                    }, status=400)

                allowed_hours = min((allocation_percent / 100) * 8, 8)
                allowed_duration = timedelta(hours=allowed_hours)

            # Cumulative hours calculation
            key = (employee_code, project_code, task_code, entry_date_str)

            # Already saved entries for SAME day-task
            existing_total = sum((
                ts.worked_hours for ts in EmployeeTimesheet.objects.filter(
                    employee_code=employee_code,
                    project_code=project_code,
                    task_description_id=task_code,
                    date=entry_date
                ).exclude(status__iexact="rejected")
            ), timedelta())

            # Remove current instance's old hours (editing)
            existing_total -= timesheet_instance.worked_hours

            # Add within-request cumulative group
            if key not in entry_group:
                entry_group[key] = worked_hours
            else:
                entry_group[key] += worked_hours

            cumulative_hours = existing_total + entry_group[key]

            if allowed_duration and cumulative_hours > allowed_duration:
                return Response({
                    "error": (
                        f"Worked hours exceeded in project {project_code} on {entry_date}. "
                        f"Allowed: {allowed_duration}, "
                        f"Attempting to add: {entry_group[key]}, Total: {cumulative_hours}"
                    )
                }, status=400)

            # Update worked_hours field
            entry["worked_hours"] = str(worked_hours)

            # Save entry
            serializer = EmployeeTimesheetSerializer(
                instance=timesheet_instance,
                data=entry,
                partial=True,
                context={"request": request}
            )

            if serializer.is_valid():
                updated_entries.append(serializer.save())
            else:
                return Response(serializer.errors, status=400)

        response_data = EmployeeTimesheetSerializer(updated_entries, many=True).data
        return Response({"message": "Timesheet updated successfully", "data": response_data}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

#get timesheet byid
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a timesheet entry by its ID.",
    responses={
        200: openapi.Response("Timesheet entry retrieved successfully.", EmployeeTimesheetSerializer),
        404: "Not Found - Timesheet entry not found."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_timesheet_by_id(request, pk):
    """
    Retrieve a specific timesheet entry by its ID.
    """
    try:
        timesheet = EmployeeTimesheet.objects.get(pk=pk)
    except EmployeeTimesheet.DoesNotExist:
        return Response({"error": "Timesheet entry not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeTimesheetSerializer(timesheet)
    return Response({"timesheet_entry": serializer.data}, status=status.HTTP_200_OK)

# GET timesheet by employee_code
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all timesheet entries for a given employee code.",
    responses={
        200: openapi.Response("Timesheet entries retrieved successfully.", EmployeeTimesheetSerializer(many=True)),
        404: "Not Found - No timesheet entries found for this employee."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_timesheets_by_employee_code(request, employee_code):
    """
    Retrieve all timesheet entries for a given employee code.
    """
    timesheets = EmployeeTimesheet.objects.filter(employee_code=employee_code)

    if not timesheets.exists():
        return Response({"error": "No timesheet entries found for this employee."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeTimesheetSerializer(timesheets, many=True)
    return Response({"timesheet_entries": serializer.data}, status=status.HTTP_200_OK)


# # Display All Timesheet Entries
@swagger_auto_schema(
    method='get',
    operation_description="Display all timesheet entries with specific fields.",
    responses={
        200: openapi.Response("Timesheet entries retrieved successfully.", EmployeeTimesheetSerializer(many=True))
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_timesheets(request):
    """
    Fetch all timesheet entries.
    """
    timesheets = EmployeeTimesheet.objects.all()
    serializer = EmployeeTimesheetSerializer(timesheets, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


#display timesheets by employee code
@swagger_auto_schema(
    method='post',
    operation_description="Display all timesheet entries for a specific employee by employee_code, month, and year.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'employee_code': openapi.Schema(type=openapi.TYPE_STRING, description="Employee code"),
            'month': openapi.Schema(type=openapi.TYPE_INTEGER, description="Month"),
            'year': openapi.Schema(type=openapi.TYPE_INTEGER, description="Year")
        }
    ),
    responses={
        200: openapi.Response("Timesheet entries retrieved successfully.", EmployeeTimesheetSerializer(many=True)),
        400: "Bad Request - Missing or invalid parameters.",
        404: "Not Found - No timesheets found."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_timesheets_by_employee_code(request):
    """
    Fetch all timesheet entries for a specific employee by employee_code, month, and year.
    """
    # Extract data from the request body
    employee_code = request.data.get('employee_code')
    month = request.data.get('month')
    year = request.data.get('year')

    # Validate the input parameters
    if not employee_code or not month or not year:
        return Response({"error": "employee_code, month, and year are required."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch timesheets for the specific employee with the given month and year
    timesheets = EmployeeTimesheet.objects.filter(employee_code=employee_code, month=month, year=year)

    # if not timesheets.exists():
    #     return Response({"message": "No timesheets found for the given employee code, month, and year."}, status=status.HTTP_404_NOT_FOUND)

    # Serialize the timesheet data
    serializer = EmployeeTimesheetSerializer(timesheets, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)

# Delete Timesheet Entry
@swagger_auto_schema(
    method='delete',
    operation_description="Delete an existing timesheet entry.",
    responses={
        200: "Timesheet entry deleted successfully.",
        404: "Timesheet not found."
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_timesheet(request, pk):
    """
    Delete a timesheet entry by its primary key (pk).
    """
    try:
        timesheet = EmployeeTimesheet.objects.get(pk=pk)
    except EmployeeTimesheet.DoesNotExist:
        return Response({"message": "Timesheet not found."}, status=status.HTTP_404_NOT_FOUND)

    timesheet.delete()
    return Response({"message": "Timesheet entry deleted successfully."}, status=status.HTTP_200_OK)

# get projects by employee
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the number of projects an employee is working on, along with project details.",
    responses={
        200: openapi.Response("Projects retrieved successfully.", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'employee_code': openapi.Schema(type=openapi.TYPE_STRING, description="Employee code"),
                'employee_name': openapi.Schema(type=openapi.TYPE_STRING, description="Employee name"),
                'project_count': openapi.Schema(type=openapi.TYPE_INTEGER, description="Number of projects"),
                'total_worked_hours': openapi.Schema(type=openapi.TYPE_STRING, description="Total worked hours in HH:MM"),
                'projects': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
                        'project_code': openapi.Schema(type=openapi.TYPE_STRING, description="Project code"),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Project description"),
                        'project_role': openapi.Schema(type=openapi.TYPE_STRING, description="Role in the project"),
                        'allocated_hours': openapi.Schema(type=openapi.TYPE_INTEGER, description="Allocated hours for the project"),
                        'total_worked_hours': openapi.Schema(type=openapi.TYPE_STRING, description="Worked hours in HH:MM format"),
                        'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project start date"),
                        'end_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Project end date"),
                    }),
                    description="List of projects with details"
                )
            }
        )),
        404: openapi.Response("Not Found - No projects found for the given employee.")
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_projects(request, employee_code):
    """
    Retrieve the number of projects an employee is working on, along with project details.
    """
    # Get projects for the given employee from ProjectTeam table
    projects = ProjectTeam.objects.filter(employee_code__employee_code=employee_code).select_related(
        'project_code', 'project_role', 'task'
    )

    if not projects.exists():
        return Response({"message": "No projects found for the given employee."}, status=status.HTTP_404_NOT_FOUND)

    # Fetch employee name from Employee model
    employee = Employee.objects.filter(employee_code=employee_code).first()
    if not employee:
        return Response({"message": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
    employee_name = employee.name  # Get the name from Employee model
    employee_designation = employee.designation

    # Fetch all approved worked hours for the employee
    employee_timesheets = EmployeeTimesheet.objects.filter(
        employee_code__employee_code=employee_code,
        status="approved"
    ).values('project_code', 'task_description').annotate(
        total_worked=Sum(Cast('worked_hours', DurationField()))
    )

    # Convert queryset to dictionary for fast lookup
    worked_hours_dict = {}
    for item in employee_timesheets:
        project_id = item['project_code']
        task_id = item['task_description']
        total_worked = item['total_worked']
        worked_hours_dict.setdefault(project_id, {})[task_id] = total_worked

    project_dict = {}
    total_worked_seconds = 0

    for project in projects:
        project_code = project.project_code.project_code
        task_id = project.task.task_code 
        task_name = project.task.task_group

        # Get worked hours for this task
        project_task_worked_hours = worked_hours_dict.get(project_code, {}).get(task_id)

        # Convert timedelta to HH:MM format
        if project_task_worked_hours:
            total_seconds = project_task_worked_hours.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            worked_hours_str = f"{hours:02}:{minutes:02}"
            total_worked_seconds += total_seconds
        else:
            worked_hours_str = "00:00"

        # Store project details if not already present
        if project_code not in project_dict:
            project_dict[project_code] = {
                "project_code": project_code,
                "description": getattr(project.project_code, 'project_description', ''),
                "project_role": project.project_role.project_role,
                "phases": []
            }

        # Append task details
        project_dict[project_code]["phases"].append({
            "phase_name": task_name,
            "allocated_hours": project.allocated_hours,
            "total_worked_hours": worked_hours_str,
            "start_date": project.start_date,
            "end_date": project.end_date,
        })

    # Convert total worked seconds to HH.MM format
    # total_hours = int(total_worked_seconds // 3600)
    # total_minutes = int((total_worked_seconds % 3600) // 60)
    # total_worked_hours_str = f"{total_hours}.{total_minutes:02}"
    # Convert total worked seconds to HH:MM format
    total_hours = int(total_worked_seconds // 3600)
    total_minutes = int((total_worked_seconds % 3600) // 60)
    total_worked_hours_str = f"{total_hours:02}:{total_minutes:02}"


    return Response({
        "employee_code": employee_code,
        "employee_name": employee_name,
        "employee_designation": employee_designation,
        "project_count": len(project_dict),
        "total_worked_hours": total_worked_hours_str,
        "projects": list(project_dict.values())
    }, status=status.HTTP_200_OK)


#GET project hours by employeecode
@swagger_auto_schema(
    method="post",
    operation_description="Retrieve project hours based on employee code.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "employee_code": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Employee code to retrieve project hours"
            )
        },
        required=["employee_code"],
    ),
    responses={
        200: openapi.Response("Project hours retrieved successfully."),
        400: "Bad Request - Validation error.",
    },
)
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_hours_by_employee(request):
    try:
        employee_code = request.data.get("employee_code")
        if not employee_code:
            return Response({"error": "employee_code is required"}, status=status.HTTP_400_BAD_REQUEST)
 
        employee = Employee.objects.filter(employee_code=employee_code).first()
        if not employee:
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
 
        employee_projects = ProjectTeam.objects.filter(employee_code=employee_code).select_related("project_code", "task")
        if not employee_projects.exists():
            return Response({"message": "No project allocation found for the given employee"}, status=status.HTTP_200_OK)
 
        projects_dict = {}
 
        for project in employee_projects:
            project_code = project.project_code.project_code
            project_name = project.project_code.project_description
            phase_name = project.task.task_group
            allocated_hours = project.allocated_hours
            # Approved timesheets
            approved_timesheets = EmployeeTimesheet.objects.filter(
                employee_code=employee_code,
                project_code=project.project_code,
                task_description=project.task,
                status='approved'
            )
            open_timesheets = EmployeeTimesheet.objects.filter(
                employee_code=employee_code,
                project_code=project.project_code,
                task_description=project.task,
                status='open'
            )
 
            def format_timedelta(td):
                total_seconds = int(td.total_seconds())
                hours, minutes = divmod(total_seconds // 60, 60)
                return f"{hours:02d}:{minutes:02d}"
           
            approved_seconds = sum(
                ts.worked_hours.total_seconds() for ts in approved_timesheets if ts.worked_hours
            )
            open_seconds = sum(
                ts.worked_hours.total_seconds() for ts in open_timesheets if ts.worked_hours
            )  
            total_seconds = approved_seconds + open_seconds
 
            total_worked_hours = format_timedelta(timedelta(seconds=approved_seconds))
            worked_hours_in_hours = total_seconds / 3600
 
            balance_hours = round(allocated_hours - worked_hours_in_hours, 2)
 
            # Fetch PhaseAllocation to get phase start/end
            phase_allocation = PhaseAllocation.objects.filter(
                project_code=project.project_code,
                task=project.task
            ).first()
 
            phase_start_date = phase_allocation.start_date if phase_allocation else None
            phase_end_date = phase_allocation.end_date if phase_allocation else None
 
            # Fetch PhaseTeamAllocation for this employee to get allocation dates
            phase_team_alloc = PhaseTeamAllocation.objects.filter(
                employee=employee,
                project=project.project_code,
                task=project.task
            ).first()
 
            allocation_start_date = phase_team_alloc.allocation_start_date if phase_team_alloc else None
            allocation_end_date = phase_team_alloc.allocation_end_date if phase_team_alloc else None
            allocation_percent = phase_team_alloc.allocation_percent if phase_team_alloc else 0

            # RB001 Internal Project fallback → use phase dates
            if project_code == "RB001" and not phase_team_alloc:
                allocation_start_date = phase_start_date
                allocation_end_date = phase_end_date

 
            latest_history = (
                phase_team_alloc.history
                .filter(updated_by=employee_code)
                .order_by('-updated_at')
                .first() if phase_team_alloc else None
            )
            if latest_history:
                allocation_start_date = latest_history.allocation_start_date
                allocation_end_date = latest_history.allocation_end_date
                allocation_percent = latest_history.allocation_percent
 
            phase_id = project.task.task_code
 
            if project_code not in projects_dict:
                projects_dict[project_code] = {
                    "project_code": project_code,
                    "project_name": project_name,
                    "phases": []
                }
 
            projects_dict[project_code]["phases"].append({
                "phase_id": phase_id,
                "phase_name": phase_name,
                "allocated_hours": allocated_hours,
                "worked_hours": total_worked_hours,
                "balance_hours": balance_hours,
                "phase_start_date": phase_start_date,
                "phase_end_date": phase_end_date,
                "allocation_start_date": allocation_start_date,
                "allocation_end_date": allocation_end_date,
                "allocation_percent": allocation_percent,
            })
 
        response_data = {
            "employee_id": employee.employee_code,
            "employee_name": employee.name,
            "projects": list(projects_dict.values()),
        }
 
        return Response({"message": "Project hours retrieved successfully", "data": response_data}, status=status.HTTP_200_OK)
 
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

#sent mail to employee
# @swagger_auto_schema(
#     method="post",
#     operation_description="Retrieve missed timesheet dates based on employee code.",
#     request_body=openapi.Schema(
#         type=openapi.TYPE_OBJECT,
#         properties={
#             "employee_code": openapi.Schema(
#                 type=openapi.TYPE_STRING,
#                 description="Employee code to retrieve missed timesheet dates"
#             )
#         },
#         required=["employee_code"],
#     ),
#     responses={
#         200: openapi.Response("Missed timesheet dates retrieved successfully."),
#         400: "Bad Request - Validation error.",
#     },
# )
# @api_view(["POST"])
# def get_missed_timesheet_dates(request):
#     try:
#         employee_code = request.data.get("employee_code")

#         if not employee_code:
#             return Response({"error": "employee_code is required"}, status=status.HTTP_400_BAD_REQUEST)

#         # Get employee
#         employee = Employee.objects.filter(employee_code=employee_code).first()
#         if not employee:
#             return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Get all projects assigned to employee
#         employee_projects = ProjectTeam.objects.filter(employee_code=employee_code).select_related("project_code")

#         if not employee_projects.exists():
#             return Response({"message": "No project allocations found for this employee"}, status=status.HTTP_200_OK)

#         response_list = []

#         for emp_proj in employee_projects:
#             project = emp_proj.project_code
#             allocated_from = emp_proj.start_date  # or your actual field name
#             allocated_to = emp_proj.end_date or timezone.now().date()

#             # Ensure allocated_to is not in the future
#             allocated_to = min(allocated_to, timezone.now().date())  # Limit the end date to today

#             # Get worked dates from timesheets
#             worked_dates = set(
#                 EmployeeTimesheet.objects.filter(
#                     employee_code=employee_code,
#                     project_code=project,
#                     status="approved"
#                 ).values_list("date", flat=True)
#             )

#             # Generate expected date range, ensuring that no future dates are included
#             all_dates = [
#                 (allocated_from + timedelta(days=i))
#                 for i in range((allocated_to - allocated_from).days + 1)
#                 if (allocated_from + timedelta(days=i)).weekday() < 5  # Mon–Fri only
#                 and (allocated_from + timedelta(days=i)) <= timezone.now().date()  # Ensure date is not in the future
#             ]

#             missed_dates_with_hours = []

#             # Check each date in the expected range
#             for date in all_dates:
#                 date_str = str(date)
#                 worked_hours = None

#                 # If the date is in the worked_dates set, fetch the worked_hours from the timesheet
#                 # In the loop where worked_hours is calculated
#                 if date in worked_dates:
#                     worked_entry = EmployeeTimesheet.objects.filter(
#                         employee_code=employee_code,
#                         project_code=project,
#                         status="approved",
#                         date=date
#                     ).first()

#                     # Assuming worked_hours is a timedelta, extract the total hours as float
#                     if worked_entry and worked_entry.worked_hours:
#                         # If worked_hours is a timedelta, we convert it to hours
#                         if isinstance(worked_entry.worked_hours, timedelta):
#                             worked_hours = round(worked_entry.worked_hours.total_seconds() / 3600.0, 2)
#                         else:
#                             worked_hours = float(worked_entry.worked_hours)  # If it's already a number
#                     else:
#                         worked_hours = 0
#                 else:
#                     worked_hours = 0


#                 # Calculate missed hours (assuming an 8-hour work day)
#                 expected_hours = 8  # Or fetch this dynamically if needed
#                 missed_hours = expected_hours - worked_hours

#                 missed_dates_with_hours.append({
#                     "missed_date": date_str,
#                     "worked_hours": worked_hours,
#                     "missed_hours": missed_hours
#                 })

#             response_list.append({
#                 "project_code": project.project_code,
#                 "project_name": project.project_description,
#                 "missed_dates": missed_dates_with_hours
#             })

#         # Email notification
#         try:
#             user_profile = UserProfile.objects.filter(user_id=employee_code).first()

#             if user_profile and user_profile.email and response_list:
#                 subject = "Missed Timesheet Summary"

#                 message_body = f"""
#                 <p>Hi {escape(employee.name)},</p>

#                 <p>Here is the summary of your missed timesheet entries:</p>

#                 <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;">
#                 <thead style="background-color: #f2f2f2; font-weight: bold;">
#                     <tr>
#                         <th>Project Code</th>
#                         <th>Project Name</th>
#                         <th>Missed Date</th>
#                         <th>Logged Hours</th>
#                     </tr>
#                 </thead>
#                 <tbody>
#                 """

#                 #  Sort by project_code and then project_name
#                 sorted_response_list = sorted(response_list, key=lambda x: (x['project_code'], x['project_name']))

#                 for project_data in sorted_response_list:
#                     project_code = project_data['project_code']
#                     project_name = escape(project_data['project_name'])
#                     missed_dates = sorted(project_data['missed_dates'], key=lambda x: x['missed_date'])

#                     for date_info in missed_dates:
#                         missed_date = date_info['missed_date']
#                         if not isinstance(missed_date, str):
#                             missed_date = missed_date.strftime("%Y-%m-%d")

#                         logged_hours = round(date_info['worked_hours'], 2)

#                         message_body += f"""
#                             <tr>
#                                 <td>{project_code}</td>
#                                 <td>{project_name}</td>
#                                 <td>{missed_date}</td>
#                                 <td style="text-align:right">{logged_hours}</td>
#                             </tr>
#                         """

#                 message_body += """
#                 </tbody>
#                 </table>

#                 <p>Please ensure to fill the missing entries at the earliest.</p>
#                 <p>This is system generated report. Please donot reply.</p>

#                 <p>Best regards,<br>PMO ROBOXA</p>
#                 """

#                 email = EmailMessage(
#                     subject=subject,
#                     body=message_body,
#                     from_email=settings.DEFAULT_FROM_EMAIL,
#                     to=[user_profile.email]
#                 )
#                 email.content_subtype = "html"
#                 email.send()

#         except Exception as mail_err:
#             print(f"Email notification failed: {mail_err}")

#         return Response({
#             "message": "Missed timesheet dates retrieved successfully",
#             "data": {
#                 "employee_code": employee.employee_code,
#                 "employee_name": employee.name,
#                 "projects": response_list
#             }
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='get',
    operation_summary="Employee Utilization Report with Detailed Projects and Tasks",
    operation_description="""
        Returns billable and non-billable worked hours (and utilization %) per employee 
        for a given date range, along with detailed worked hours for each project and task.
    """,
    manual_parameters=[
        openapi.Parameter('employee_code', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
        openapi.Parameter('from_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('to_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(description="Utilization data with project and task breakdown"),
        400: "Missing or invalid input"
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def emp_utilization_report(request):
    employee_code = request.query_params.get('employee_code')
    from_date = request.query_params.get('from_date')
    to_date = request.query_params.get('to_date')

    if not all([from_date, to_date]):
        return Response({"error": "Missing required parameters: from_date, to_date"}, status=400)

    try:
        from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

    non_billable_project_code = "RB001"
    non_billable_keyword = "Internal Project"

    qs = EmployeeTimesheet.objects.filter(
        date__range=(from_date, to_date),
        status__iexact="Approved"
    )

    if employee_code:
        qs = qs.filter(employee_code__employee_code=employee_code)

    grouped_data = {}

    for entry in qs:
        emp_code = entry.employee_code.employee_code
        emp_name = entry.employee_code.name
        project_code = (entry.project_code.project_code or "").strip().upper()
        project_desc = (entry.project_code.project_description or "").strip()
        task_desc = (entry.task_description.description or "").strip()
        new_desc = (entry.new_description or "").strip()
        worked = entry.worked_hours if entry.worked_hours else timedelta()

        if emp_code not in grouped_data:
            grouped_data[emp_code] = {
                "employee_code": emp_code,
                "employee_name": emp_name,
                "billable": timedelta(),
                "non_billable": timedelta(),
                "projects": {}
            }

        if project_code == non_billable_project_code or non_billable_keyword in project_desc.lower():
            grouped_data[emp_code]["non_billable"] += worked
            entry_type = "non-billable"
        else:
            grouped_data[emp_code]["billable"] += worked
            entry_type = "billable"

        project_key = (project_code, project_desc)
        if project_key not in grouped_data[emp_code]["projects"]:
            grouped_data[emp_code]["projects"][project_key] = {
                "type": entry_type,
                "tasks": {}
            }

        task_key = (task_desc, new_desc)
        if task_key not in grouped_data[emp_code]["projects"][project_key]["tasks"]:
            grouped_data[emp_code]["projects"][project_key]["tasks"][task_key] = timedelta()

        grouped_data[emp_code]["projects"][project_key]["tasks"][task_key] += worked

    def format_duration(td):
        total_minutes = int(td.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02d}:{minutes:02d}"

    def duration_to_decimal(td):
        total_minutes = int(td.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return float(f"{hours + minutes / 60:.2f}")  # Always 2 decimals
 

    response_data = []
    total_billable = timedelta()
    total_non_billable = timedelta()
    total_expected_hours = 0

    for emp_data in grouped_data.values():
        # working days
        num_working_days = sum(1 for d in range((to_date - from_date).days + 1)
                               if (from_date + timedelta(days=d)).weekday() < 5)

        expected_hours = num_working_days * 8
        expected_seconds = expected_hours * 3600
        billable_seconds = emp_data["billable"].total_seconds()
        utilization = (billable_seconds / expected_seconds * 100) if expected_seconds else 0

        # update totals
        total_billable += emp_data["billable"]
        total_non_billable += emp_data["non_billable"]
        total_expected_hours += expected_hours

        projects_list = []
        for (code, desc), project_info in emp_data["projects"].items():
            tasks_list = []
            for (task_desc, new_desc), duration in project_info["tasks"].items():
                tasks_list.append({
                    "task_description": task_desc,
                    "new_description": new_desc,
                    "worked_hours": format_duration(duration)
                })

            projects_list.append({
                "project_code": code,
                "project_description": desc,
                "type": project_info["type"],
                "tasks": tasks_list
            })

        response_data.append({
            "employee_code": emp_data["employee_code"],
            "employee_name": emp_data["employee_name"],
            "billable_hours": format_duration(emp_data["billable"]),
            "non_billable_hours": format_duration(emp_data["non_billable"]),
            "expected_hours": expected_hours,
            "utilization_percentage": f"{utilization:.2f}%",
            "projects": projects_list
        })

    final_response = {
        "chartData": {
            "labels": [
                "Expected Hours",
                "Billable Hours",
                "Non Billable Hours"
            ],
            "values": [
                total_expected_hours,
                f"{duration_to_decimal(total_billable):.2f}",
                f"{duration_to_decimal(total_non_billable):.2f}"
            ]
        },
        "tableData": response_data
    }

    return Response(final_response, status=200)

@swagger_auto_schema(

    method='get',

    manual_parameters=[

        openapi.Parameter(

            'project_code',

            openapi.IN_QUERY,

            description="Filter by project code (e.g., SG001,SG002) - multiple codes separated by commas",

            type=openapi.TYPE_STRING,

            required=True,

        ),

        openapi.Parameter(

            'date_range',

            openapi.IN_QUERY,

            description="Optional: Number of days from today to check for employee end dates (default: 90)",

            type=openapi.TYPE_INTEGER,

            required=False,

        ),

    ],

    responses={200: "Project and employee list", 404: "Project not found"},

)

@api_view(['GET'])

@permission_classes([IsAuthenticated])

def get_project_duration_report(request):

    """

    Defaults to 90 days if not provided.

    Accepts multiple project codes separated by commas.

    """

    project_code = request.query_params.get("project_code")

    date_range_param = request.query_params.get("date_range")
 
    if not project_code:

        return Response(

            {"error": "project_code is required."},

            status=status.HTTP_400_BAD_REQUEST,

        )
 
    # Split project codes by comma and remove any empty strings or whitespace

    project_codes = [code.strip() for code in project_code.split(',') if code.strip()]

    if not project_codes:

        return Response(

            {"error": "At least one valid project_code is required."},

            status=status.HTTP_400_BAD_REQUEST,

        )
 
    try:

        # Get all projects that match the provided codes

        projects = Project.objects.filter(project_code__in=project_codes)

        # Check if all requested projects were found

        found_codes = set(projects.values_list('project_code', flat=True))

        not_found_codes = set(project_codes) - found_codes

        if not_found_codes:

            return Response(

                {"error": f"Project(s) with code(s) {', '.join(not_found_codes)} not found."},

                status=status.HTTP_404_NOT_FOUND,

            )

    except Project.DoesNotExist:

        return Response(

            {"error": f"Project with code '{project_code}' not found."},

            status=status.HTTP_404_NOT_FOUND,

        )
 
    today = date.today()

    try:

        date_range = int(date_range_param) if date_range_param else 90

    except ValueError:

        return Response(

            {"error": "date_range must be an integer (number of days)."},

            status=status.HTTP_400_BAD_REQUEST,

        )
 
    cutoff_date = today + timedelta(days=date_range)
 
    # Get employees for all projects

    employees = ProjectTeam.objects.select_related("employee_code", "project_code").filter(

        project_code__in=projects,

        end_date__range=(today, cutoff_date)

    ).order_by("project_code", "end_date", "employee_name")
 
    if not employees.exists():

        return Response(

            {"message": f"No employees ending within {date_range} days for the specified projects."},

            status=status.HTTP_200_OK,

        )
 
    response_data = {"employees": []}
 
    for emp in employees:

        emp_obj = emp.employee_code

        project_obj = emp.project_code

        end_date = emp.end_date
 
        # latest allocation record

        allocation_record = (

            ProjectTeamAllocationHistory.objects

            .filter(allocation__employee_code=emp_obj, allocation__project_code=project_obj)

            .order_by("-updated_at")

            .first()

        )
 
        # project specific flag

        project_specific = "yes" if ProjectTeam.objects.filter(

            employee_code=emp_obj, project_code=project_obj

        ).exists() else "no"
 
        # contractor flag

        is_contractor = (

            hasattr(emp_obj, "employment_type")

            and emp_obj.employment_type

            and "contract" in emp_obj.employment_type.lower()

        )
 
        response_data["employees"].append({

            "project_name": project_obj.project_description,

            "project_code": project_obj.project_code,

            "date_range_days": date_range,

            "employee_no": emp_obj.employee_code,

            "employee_name": emp.employee_name,

            "project_specific": project_specific,

            "contractor": "yes" if is_contractor else "no",

            "skillset_primary": getattr(emp_obj, "primary_skill", []),

            "skillset_secondary": getattr(emp_obj, "secondary_skill", []),

            "allocation_percent": (

                allocation_record.allocation_percent if allocation_record else None

            ),

            "employee_end_date": end_date.strftime("%Y-%m-%d") if end_date else None,

        })
 
    return Response(response_data, status=status.HTTP_200_OK)
 
@swagger_auto_schema(
    method='get',
    operation_summary="Get All Countries List",
    operation_description="Returns a comprehensive list of all countries in the world sorted alphabetically.",
    responses={
        200: openapi.Response(
            description="List of all countries",
            examples={
                "application/json": {
                    "success": True,
                    "message": "Countries retrieved successfully",
                    "data": [
                        {"id": 1, "name": "Afghanistan"},
                        {"id": 2, "name": "Albania"},
                        {"id": 85, "name": "India"}
                    ]
                }
            }
        )
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_countries_list(request):
    """
    Returns complete list of world countries with ID and name, sorted alphabetically.
    """
    country_names = [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina",
        "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
        "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
        "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
        "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde",
        "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
        "Congo (Brazzaville)", "Congo (Kinshasa)", "Costa Rica", "Croatia", "Cuba",
        "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
        "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
        "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia",
        "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
        "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran",
        "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan",
        "Kenya", "Kiribati", "Korea (North)", "Korea (South)", "Kuwait", "Kyrgyzstan",
        "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
        "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
        "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia",
        "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
        "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
        "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama",
        "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
        "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
        "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
        "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore",
        "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan",
        "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
        "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
        "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
        "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
        "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
        "Zimbabwe"
    ]
    
    country_data = [
        {"id": idx + 1, "name": name} 
        for idx, name in enumerate(country_names)
    ]
    
    return Response({
        "success": True,
        "message": "Countries retrieved successfully",
        "data": country_data
    }, status=200)
