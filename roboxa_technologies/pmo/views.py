from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import timedelta,datetime
from django.db.models import Sum, Value,FloatField,Max,F,Count,OuterRef,Subquery, Min
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import Coalesce
from .models import Project,ProjectTeam,ProjectTeamAllocation,ProjectTeamAllocationHistory
from master_data.models import ProjectTasks
from employee.models import EmployeeTimesheet,Employee
from pmo.models import PhaseAllocation,PhaseTeamAllocation,PhaseTeamAllocationHistory
from rest_framework import generics
from datetime import date
from collections import defaultdict
from collections import Counter
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.mail import send_mail
from user_management.models import UserProfile
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from django.shortcuts import get_object_or_404
from .serializers import ProjectCreateSerializer, ProjectListSerializer, EditProjectSerializer, ProjectTeamSerializer,ProjectTeamCreateSerializer,PhaseAllocationSerializer,ProjectTeamAllocationSerializer, ProjectEmployeeDetailsSerializer
from itertools import combinations
from django.utils.dateparse import parse_date
from django.db.models import Max
from django.db.models import OuterRef, Subquery


@swagger_auto_schema(
    method='post',
    operation_description="Create a new project assignment.",
    request_body=ProjectCreateSerializer,
    responses={201: openapi.Response("Project created successfully.", ProjectCreateSerializer),
               400: "Bad Request - Validation error."}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_project(request):
    serializer = ProjectCreateSerializer(data=request.data)

    if serializer.is_valid():
        # Extract project details
        budgeted_hours = serializer.validated_data.get("budgeted_hours", 0)

        # Set allocated_hours to 0 (it will be updated in add_project_team)
        serializer.validated_data["allocated_hours"] = 0

        # Optionally enforce management value even if user tries to change it
        serializer.validated_data["management"] = "Sudhakara Varma Yarramraju"

        # Save the project
        project = serializer.save()

        return Response({
            "message": "Project created successfully.",
            "data": ProjectCreateSerializer(project).data
        }, status=status.HTTP_201_CREATED)
     # Check for duplicate project_code error and return a custom message
    if "project_code" in serializer.errors:
        project_code = request.data.get("project_code", "unknown")
        return Response(
            {"error": f"Project with this project code {project_code} already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

def calculate_allocated_hours(project_data):
    """
    Calculate the total allocated hours for the project based on the employees in the project.
    """
    project_code = project_data.get("project_code")
    
    # Try fetching assigned employees from ProjectTeam
    project_team_members = ProjectTeam.objects.filter(project_code=project_code)
    
    if project_team_members.exists():
        allocated_hours = sum(member.allocated_hours for member in project_team_members)
    else:
        # Fallback: Use allocated_hours from request data if no team members exist yet
        allocated_hours = project_data.get("allocated_hours", 0)  

    return allocated_hours

def calculate_total_worked_hours(project_code):
    # Aggregate the total approved worked hours for the project
    total_time = EmployeeTimesheet.objects.filter(
        project_code=project_code,
        status='approved'
    ).aggregate(Sum('worked_hours'))['worked_hours__sum']

    if total_time is None:
        return "00:00"  # Default if no approved hours logged

    # Convert total_time to total_seconds regardless of type
    if isinstance(total_time, timedelta):
        total_seconds = int(total_time.total_seconds())
    elif isinstance(total_time, (float, int)):
        total_seconds = int(total_time * 3600)
    else:
        raise ValueError(f"Unexpected data type for worked_hours: {type(total_time)}")

    # Convert total seconds to HH:MM format
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    # Return without capping the hour digits
    return f"{hours}:{minutes:02d}"



#get projects
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all projects with updated worked hours",
    responses={200: openapi.Response("Projects retrieved successfully.", ProjectListSerializer(many=True))}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_projects(request):
    projects = Project.objects.all()

    for project in projects:
        total_allocated_hours = ProjectTeam.objects.filter(
            project_code=project.project_code
        ).aggregate(
            total_allocated=Coalesce(Sum('allocated_hours'), Value(0))
        )['total_allocated']

        total_hours = calculate_total_worked_hours(project.project_code)

        #  Ensure `worked_hours` is stored as "HH:MM"
        formatted_hours = total_hours[:5]  # Trim seconds, keeping only "HH:MM"

        if (project.worked_hours != formatted_hours or
            project.allocated_hours != total_allocated_hours):
            project.worked_hours = formatted_hours
            project.allocated_hours = total_allocated_hours
            project.save(update_fields=['worked_hours', 'allocated_hours'])


    serializer = ProjectListSerializer(projects, many=True)
    return Response({"message": "Projects retrieved successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

project_code_param = openapi.Parameter(
    'project_code',
    openapi.IN_QUERY,
    description="Project Code to filter the project",
    type=openapi.TYPE_STRING,
    required=True
)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve project details by project code",
    responses={
        200: openapi.Response("Project retrieved successfully.", ProjectListSerializer()),
        404: openapi.Response("Project not found.")
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_by_code(request, project_code):  # 
    try:
        project = Project.objects.get(project_code=project_code)
    except Project.DoesNotExist:
        return Response({"message": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    total_allocated_hours = ProjectTeam.objects.filter(
        project_code=project.project_code
    ).aggregate(
        total_allocated=Coalesce(Sum('allocated_hours'), Value(0))
    )['total_allocated']

    total_hours = calculate_total_worked_hours(project.project_code)
    formatted_hours = total_hours[:5]  # Keep "HH:MM" format

    if (project.worked_hours != formatted_hours or
        project.allocated_hours != total_allocated_hours):
        project.worked_hours = formatted_hours
        project.allocated_hours = total_allocated_hours
        project.save(update_fields=['worked_hours', 'allocated_hours'])

    serializer = ProjectListSerializer(project)
    return Response({"message": "Project retrieved successfully.", "data": serializer.data}, status=status.HTTP_200_OK)


#edit project
@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing project.",
    request_body=EditProjectSerializer,
    responses={
        200: openapi.Response("Project updated successfully.", EditProjectSerializer),
        404: "Not Found - Project not found.",
        400: "Bad Request - Validation error."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_project(request, project_code):
    try:
        project = Project.objects.get(project_code=project_code)
    except Project.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()  # Make a mutable copy of the request data
    new_project_code = data.get("project_code")

    # Check if the project_code is changing
    if new_project_code and new_project_code != project_code:
        data.pop("id", None)  # Ensure no conflict with primary key
        new_project = Project.objects.create(**data)  # Create new project
        project.delete()  # Delete the old project

        return Response({"message": "Project code updated successfully.", "data": EditProjectSerializer(new_project).data},
                        status=status.HTTP_200_OK)

    # Otherwise, update normally
    serializer = EditProjectSerializer(project, data=data, partial=True)
    if serializer.is_valid():
        # Extract budgeted_hours & allocated_hours if present in update
        budgeted_hours = serializer.validated_data.get("budgeted_hours", project.budgeted_hours)
        allocated_hours = serializer.validated_data.get("allocated_hours", project.allocated_hours)

        # Validate allocated hours before saving
        if allocated_hours > budgeted_hours:
            return Response(
                {"error": "Allocated hours cannot exceed budgeted hours."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return Response({"message": "Project updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#delete project
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a project by project_code.",
    responses={200: "Project deleted successfully.", 404: "Project not found."}
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_project(request, project_code):
    try:
        project = Project.objects.get(project_code=project_code)
        project.delete()
        return Response({"message": "Project deleted successfully."}, status=status.HTTP_200_OK)
    except Project.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

#add project team
@swagger_auto_schema(
    method='post',
    operation_description="Create project team assignments for one or more employees.",
    request_body=ProjectTeamCreateSerializer(many=True),
    responses={201: openapi.Response("Project team(s) created successfully.", ProjectTeamCreateSerializer(many=True)),
               400: "Bad Request - Validation error."}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_project_team(request):
    """
    Add employees to a project team and update allocated hours in Project and PhaseAllocation.
    """
    try:
        is_bulk = isinstance(request.data, list)
        serializer = ProjectTeamCreateSerializer(data=request.data, many=is_bulk)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        project_code = request.data[0]["project_code"] if is_bulk else request.data["project_code"]

        # Ensure the project exists
        project = Project.objects.filter(project_code=project_code).first()
        if not project:
            return Response({"error": f"Project with code {project_code} not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate total new allocated hours from request
        total_new_allocated_hours = sum(emp["allocated_hours"] for emp in serializer.validated_data)

        # Ensure project-level allocation does not exceed budget
        available_project_hours = project.budgeted_hours - project.allocated_hours
        if total_new_allocated_hours > available_project_hours:
            return Response(
                {"error": f"Total allocated hours ({total_new_allocated_hours}) exceed available project hours ({available_project_hours})."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # **Validate allocated_hours per PhaseAllocation BEFORE saving**
        task_allocations = {}  # Dictionary to track total allocated hours per task

        for emp in serializer.validated_data:
            employee_code = emp["employee_code"]
            employee_name = emp["employee_name"]

            # Step 1: Get active project codes
            today = timezone.now().date()

            # Step 1: Get all active project codes where employee is assigned
            active_project_codes = ProjectTeam.objects.filter(
                employee_code=employee_code,
                end_date__gte=today
            ).values_list('project_code', flat=True)

            internal_project_code = "RB001"

            # STEP 1: Calculate existing allocation for this employee in this project (excluding deleted teams)
            existing_allocation_percent = ProjectTeamAllocation.objects.filter(
                employee_code=employee_code,
                project_code=project_code
            ).exclude(
                project_code__project_code=internal_project_code
            ).aggregate(
                total=Coalesce(Sum('allocation_percent'), Value(0), output_field=FloatField())
            )['total'] or 0

            # STEP 2: Add the new allocation from request
            new_allocation_percent = emp.get("allocation_percent", 0)

            # STEP 3: Check if this exceeds limit
            if existing_allocation_percent + new_allocation_percent > 100:
                return Response({
                    "error": f"Cannot assign employee '{employee_name}' to project '{project_code}'. "
                            f"Existing allocation: {existing_allocation_percent}%. "
                            f"Requested: {new_allocation_percent}%. Exceeds 100%."
                }, status=400)


            task_obj = emp["task"]
            task = task_obj.task_code if hasattr(task_obj, 'task_code') else task_obj
            phase_allocation = PhaseAllocation.objects.filter(
                task=task,
                project_code=emp["project_code"]
            ).first()

            if not phase_allocation:
                return Response(
                            {"error": f"No phase found for project {project_code} with task {{task}}"},
                            status=400
                        )


            # **Fetch existing allocated hours for this task**
            current_allocated_hours = ProjectTeam.objects.filter(
                task=task,
                project_code=emp["project_code"]
            ).aggregate(total_allocated=Coalesce(Sum('allocated_hours'), Value(0)))['total_allocated']

            # **Accumulate new allocations for this task**
            if task not in task_allocations:
                task_allocations[task] = 0
            task_allocations[task] += emp["allocated_hours"]

            # **Check total allocation against budget**
            total_task_allocation = current_allocated_hours + task_allocations[task]
            if total_task_allocation > phase_allocation.budgeted_hours:
                # Fetch task group (name) using task code
                task_obj = ProjectTasks.objects.filter(task_code=task).first()
                task_name = task_obj.task_group if task_obj else f"task {task}"

                return Response({
                    "error": f"Cannot allocate {emp['allocated_hours']} hours for phase {task_name}."
                }, status=status.HTTP_400_BAD_REQUEST)
  

        # **Save ProjectTeam records**
        project_teams = []
        for emp_data in serializer.validated_data:
            project_team = ProjectTeam.objects.create(
                employee_name=emp_data["employee_name"],
                designation=emp_data["designation"],
                start_date=emp_data["start_date"],
                end_date=emp_data["end_date"],
                allocated_hours=emp_data["allocated_hours"],
                project_code=emp_data["project_code"],
                employee_code=emp_data["employee_code"],
                project_role=emp_data["project_role"],
                task=emp_data["task"]
                # task = task_obj
                
            )
            project_teams.append(project_team)
            

        # **Update project allocated hours**
        project.allocated_hours += total_new_allocated_hours
        project.save()

        # **Update PhaseAllocation allocated_hours**
        for team in project_teams:
            phase_allocation = PhaseAllocation.objects.filter(
                task=team.task,
                project_code=team.project_code
            ).first()
            if phase_allocation:
                phase_allocation.allocated_hours += team.allocated_hours
                phase_allocation.save()

        for team in project_teams:
            try:
                # Check if this is the first time employee is added to the project
                existing_assignments = ProjectTeam.objects.filter(
                    employee_code=team.employee_code,
                    project_code=team.project_code
                ).exclude(id=team.id)

                if existing_assignments.exists():
                    # Skip sending mail if already assigned earlier
                    continue

            # try:
                print(f"Checking UserProfile for employee_code = {team.employee_code.employee_code}")

                user_profile = UserProfile.objects.filter(user_id=team.employee_code.employee_code).first()

                if not user_profile:
                    # print(f" No UserProfile found for employee_code = {team.employee_code.employee_code}")
                    continue

                if not user_profile.email:
                    # print(f" No email found for user_id = {team.employee_code.employee_code}")
                    continue

                # STEP 5: Build HTML email content
                html_message = f"""
                <p>Hi {team.employee_name},</p>

                <p>You have been assigned to the following project:</p>

                <p>
                    <strong>Project:</strong> {team.project_code.project_description}<br>
                    <strong>Project Code:</strong> {team.project_code.project_code}<br>
                </p>

                <p>Best regards,<br>
                <strong>ROBOXA PMO.</strong></p>
            """

                plain_message = strip_tags(html_message)

                subject = "Project Assignment Notification"

                # STEP 6: Send email
                email_msg = EmailMultiAlternatives(
                    subject=subject.strip(),
                    body=plain_message,
                    from_email=settings.EMAIL_HOST_USER,  # or None to use DEFAULT_FROM_EMAIL
                    to=[user_profile.email]
                )
                email_msg.attach_alternative(html_message, "text/html")
                email_msg.send()
                # print(f" Mail sent to {user_profile.email}")

            except Exception as e:
                print(f" Failed to send mail for {team.employee_name}: {e}")

        return Response({
            "message": "project team created successfully.",
            "data": ProjectTeamCreateSerializer(project_teams, many=is_bulk).data
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def update_phase_allocation(project_code, task):
    total_allocated = ProjectTeam.objects.filter(
        project_code=project_code,
        task=task
    ).aggregate(total=Sum('allocated_hours'))['total'] or 0

    phase_allocation, _ = PhaseAllocation.objects.get_or_create(
        project_code=project_code,
        task=task,
        defaults={'budgeted_hours': 0, 'allocated_hours': 0}
    )
    phase_allocation.allocated_hours = total_allocated
    phase_allocation.save()

#update allocated hours in project
def update_project_allocation(project_code):
    total_allocated = ProjectTeam.objects.filter(
        project_code=project_code
    ).aggregate(total=Sum('allocated_hours'))['total'] or 0

    Project.objects.filter(project_code=project_code).update(allocated_hours=total_allocated)


#edit projectteam
@swagger_auto_schema(
    method='put',
    operation_description="Update project team assignments for one or more employees.",
    request_body=ProjectTeamCreateSerializer(many=True),
    responses={
        200: openapi.Response("Project team(s) updated successfully.", ProjectTeamCreateSerializer(many=True)),
        400: "Bad Request - Validation error.",
        404: "Not Found - One or more project team entries were not found."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_project_team(request):
    data = request.data
    if not isinstance(data, list):
        return Response({"error": "Input must be a list of objects"}, status=400)
 
    errors = []
    success = []
    update_groups = defaultdict(list)
 
    for item in data:
        update_groups[(item["project_code"], item["task"])].append(item)
 
    old_tasks_updated = set()
    new_tasks_updated = set()
 
    try:
        with transaction.atomic():
            for (project_code, task), updates in update_groups.items():
                phase_allocation = PhaseAllocation.objects.filter(project_code=project_code, task=task).first()
                if not phase_allocation:
                    errors.append({"error": f"No PhaseAllocation found for project {project_code}, task {task}"})
                    continue
 
                instance_map = {}
                new_requested_hours = 0
 
                for item in updates:
                    try:
                        instance = ProjectTeam.objects.get(id=item["id"])
                        old_task = instance.task
                        old_allocated_hours = instance.allocated_hours
 
                        try:
                            new_hours = float(str(item.get("allocated_hours", 0)).strip())
                        except (ValueError, TypeError):
                            errors.append({
                                "error": f"Invalid allocated_hours value for ProjectTeam id {item['id']}. Got: {item.get('allocated_hours')}"
                            })
                            continue
 
                        new_requested_hours += new_hours
                        instance_map[item["id"]] = (instance, new_hours, old_task, old_allocated_hours)
 
                    except ProjectTeam.DoesNotExist:
                        errors.append({"error": f"ProjectTeam with id {item['id']} not found."})
                    except (ValueError, TypeError):
                        errors.append({"error": f"Invalid allocated_hours value for ProjectTeam id {item['id']}."})
 
                existing_allocated = ProjectTeam.objects.filter(
                    project_code=project_code,
                    task=task
                ).exclude(id__in=[item["id"] for item in updates]).aggregate(
                    total=Sum('allocated_hours')
                )["total"] or 0
 
                total_after_update = existing_allocated + new_requested_hours
 
                if total_after_update > phase_allocation.budgeted_hours:
                    errors.append({
                        "non_field_errors": [
                            f"Total allocated hours ({total_after_update}) exceed budgeted hours ({phase_allocation.budgeted_hours}) "
                            f"for project {project_code} and task {task}."
                        ]
                    })
                    continue
 
                for item in updates:
                    instance = ProjectTeam.objects.get(id=item.get("id"))
                    original_employee_name = instance.employee_name  # Save original name
                    original_employee_code = instance.employee_code.employee_code  # Access the actual employee_code string
                    instance, new_hours, old_task, old_allocated_hours = instance_map.get(item["id"], (None, 0, None, 0))
                    if not instance:
                        continue
                    # # Check for timesheet
                    existing_timesheets = EmployeeTimesheet.objects.filter(
                        employee_code=instance.employee_code,
                        project_code=instance.project_code,
                        task_description=instance.task
                    ).exists()

                    serializer = ProjectTeamCreateSerializer(instance, data=item, partial=True)
                    if serializer.is_valid():
                        new_project_code = item.get("project_code", instance.project_code)
                        new_task = item.get("task", instance.task)
                        employee_code = item.get("employee_code", instance.employee_code)
                        #  Check for task change before saving
                        #  Only block if task is changing and timesheets exist for the current (old) task
                        if "task" in item and item["task"] != instance.task.task_code:
                            timesheet_exists = EmployeeTimesheet.objects.filter(
                                employee_code=instance.employee_code,
                                project_code=instance.project_code,
                                task_description=instance.task
                            ).exists()
                            if timesheet_exists:
                                errors.append({
                                    "error": f"Cannot change phase for employee '{instance.employee_name}', timesheet entries already exist for the current phase '{instance.task.task_code} - {instance.task.task_group}'."
                                })
                                continue
 
 
                        # Check if PhaseAllocation exists
                        if not PhaseAllocation.objects.filter(project_code=new_project_code, task=new_task).exists():
                            errors.append({
                                "error": f"PhaseAllocation not found for updated project {new_project_code}, task {new_task}."
                            })
                            continue

                        if employee_code != str(instance.employee_code) and \
                            not Employee.objects.filter(employee_code=employee_code).exists():
                                errors.append({
                                    "error": f"Employee '{employee_code}' does not exist."
                                })
                                continue
                    
                       
                        # Check end_date against existing timesheets
                        new_end_date = item.get("end_date")
 
                        if new_end_date:
                            # Convert string to date if necessary
                            if isinstance(new_end_date, str):
                                new_end_date = datetime.strptime(new_end_date, "%Y-%m-%d").date()
 
                            latest_timesheet_date = EmployeeTimesheet.objects.filter(
                                employee_code=instance.employee_code,
                                project_code=instance.project_code,
                                task_description=instance.task
                            ).aggregate(latest=Max("date"))["latest"]
 
                            if latest_timesheet_date and new_end_date < latest_timesheet_date:
                                errors.append({
                                    "error": f"Cannot update end_date to {new_end_date}. "
                                            f"Timesheet entries exist until {latest_timesheet_date}."
                                })
                                continue
 
                        # Block update if allocated_hours < worked_hours already logged
                        total_worked_hours = EmployeeTimesheet.objects.filter(
                            employee_code=instance.employee_code,
                            project_code=instance.project_code,
                            task_description=instance.task
                        ).aggregate(total=Sum('worked_hours'))["total"] or timedelta()

                        # Convert new_hours (float) to timedelta for comparison
                        new_allocated_duration = timedelta(hours=new_hours)

                        if new_allocated_duration < total_worked_hours:
                            errors.append({
                                "error": (
                                    f"Cannot reduce allocated hours to {new_hours} for employee '{instance.employee_code}', "
                                    f"already logged {total_worked_hours.total_seconds() / 3600:.2f} hours in timesheets."
                                )
                            })
                            continue
                          # Check if trying to change employee_name
                        if "employee_name" in item and item["employee_name"] != original_employee_name:
                            if existing_timesheets:
                                errors.append({
                                    "error": (
                                        f"Cannot change employee_name for ProjectTeam id {instance.id}. "
                                        f"Timesheet entries already exist for employee '{original_employee_name}'."
                                    )
                                })
                                continue
                        # Check if trying to change employee_code
                        if "employee_code" in item and item["employee_code"] != original_employee_code:
                            if existing_timesheets:
                                errors.append({
                                    "error": (
                                        f"Cannot change employee_code for ProjectTeam id {instance.id}. "
                                        f"Timesheet entries already exist for employee code '{original_employee_code}'."
                                    )
                                })
                                continue
    
                        serializer.save()
 
                        new_task = serializer.instance.task
 
                        if new_task is not None and old_task != new_task:
                            ProjectTeam.objects.filter(
                                employee_code=instance.employee_code,
                                project_code=instance.project_code,
                                task=old_task
                            ).exclude(id=instance.id).update(allocated_hours=0)
 
                            old_tasks_updated.add((instance.project_code, old_task))
                            new_tasks_updated.add((instance.project_code, new_task))
                        else:
                            new_tasks_updated.add((instance.project_code, new_task))
 
                        success.append(serializer.data)
                    else:
                        errors.append(serializer.errors)
 
            for project_code, task in old_tasks_updated:
                update_phase_allocation(project_code, task)
                update_project_allocation(project_code)
            for project_code, task in new_tasks_updated:
                update_phase_allocation(project_code, task)
                update_project_allocation(project_code)
 
        if errors:
            return Response({"errors": errors}, status=400)
        return Response({"message": "Project team successfully updated", "data": success}, status=200)
 
    except Exception as e:
        return Response({"error": str(e)}, status=500)



#delete project team
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a project team assignment.",
    responses={
        204: "No Content - Successfully deleted.",
        400: "Bad Request - Cannot delete as timesheet entries exist.",
        404: "Not Found - Project team does not exist."
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_project_team(request, pk):
    try:
        project_team = ProjectTeam.objects.get(pk=pk)

        # Check if there are timesheet entries for this employee/project/task
        timesheet_entries_exist = EmployeeTimesheet.objects.filter(
            employee_code=project_team.employee_code,
            project_code=project_team.project_code,
            task_description=project_team.task
        ).exists()

        if timesheet_entries_exist:
            return Response(
                {"error": "Cannot delete ProjectTeam entry. Timesheet entry exists for this phase."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update allocated_hours in PhaseAllocation before deletion
        phase_allocation = PhaseAllocation.objects.filter(
            project_code=project_team.project_code,
            task=project_team.task
        ).first()

        if phase_allocation:
            phase_allocation.allocated_hours = max(0, phase_allocation.allocated_hours - project_team.allocated_hours)
            phase_allocation.save()

        # Delete ProjectTeamAllocation entry
        # ProjectTeamAllocation.objects.filter(
        #     employee_code=project_team.employee_code,
        #     project_code=project_team.project_code
        # ).delete()
        #  Only delete allocation if no other team entries exist for that employee+project
        other_team_exists = ProjectTeam.objects.filter(
            employee_code=project_team.employee_code,
            project_code=project_team.project_code
        ).exclude(pk=project_team.pk).exists()

        if not other_team_exists:
            ProjectTeamAllocation.objects.filter(
                employee_code=project_team.employee_code,
                project_code=project_team.project_code
            ).delete()

        # Delete ProjectTeam entry once
        project_team.delete()

        return Response({"message": "Project team deleted successfully and allocated hours updated."}, status=status.HTTP_204_NO_CONTENT)

    except ProjectTeam.DoesNotExist:
        return Response({"error": "Project team not found."}, status=status.HTTP_404_NOT_FOUND)

#bulk delete projectteam
@swagger_auto_schema(
    method='delete',
    operation_description="Bulk delete project team assignments. If any assignment has related timesheet entries, it will be skipped.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "project_team_ids": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description="List of ProjectTeam IDs to delete"
            )
        },
        required=["project_team_ids"]
    ),
    responses={
        204: "No Content - Successfully deleted.",
        207: "Multi-Status - Some entries deleted, some skipped.",
        400: "Bad Request - Invalid input.",
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def bulk_delete_project_teams(request):
    project_team_ids = request.data.get("project_team_ids", [])
    
    if not project_team_ids or not isinstance(project_team_ids, list):
        return Response({"error": "project_team_ids must be a list of IDs."}, status=status.HTTP_400_BAD_REQUEST)

    deleted = []
    skipped = []

    for pk in project_team_ids:
        try:
            project_team = ProjectTeam.objects.get(pk=pk)

            # Check timesheet entry existence
            has_timesheet = EmployeeTimesheet.objects.filter(
                employee_code=project_team.employee_code,
                project_code=project_team.project_code,
                task_description=project_team.task
            ).exists()

            if has_timesheet:
                skipped.append({
                    "id": pk,
                    "reason": "Timesheet entries exist"
                })
                continue

            # Update PhaseAllocation allocated_hours
            phase_allocation = PhaseAllocation.objects.filter(
                project_code=project_team.project_code,
                task=project_team.task
            ).first()

            if phase_allocation:
                phase_allocation.allocated_hours = max(0, phase_allocation.allocated_hours - project_team.allocated_hours)
                phase_allocation.save()

            # Delete ProjectTeamAllocation
            ProjectTeamAllocation.objects.filter(
                employee_code=project_team.employee_code,
                project_code=project_team.project_code
            ).delete()

            # Delete ProjectTeam
            project_team.delete()
            deleted.append(pk)

        except ProjectTeam.DoesNotExist:
            skipped.append({
                "id": pk,
                "reason": "ProjectTeam not found"
            })

    if skipped:
        return Response({
            "message": "Bulk delete completed with some skipped entries.",
            "deleted_ids": deleted,
            "skipped": skipped
        }, status=status.HTTP_207_MULTI_STATUS)

    return Response({
        "message": "All project teams deleted successfully.",
        "deleted_ids": deleted
    }, status=status.HTTP_204_NO_CONTENT)

#get projectteams
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all project team assignments or filter by project, "
                          "include allocation%, total allocation%, allocation start/end dates, "
                          "and allocation history for each employee.",
    manual_parameters=[
        openapi.Parameter('project_code', openapi.IN_QUERY, description="Filter by project code", type=openapi.TYPE_STRING)
    ],
    responses={
        200: openapi.Response("Successful response", ProjectTeamSerializer(many=True)),
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_teams(request):
    project_code = request.query_params.get('project_code')
 
    if project_code:
        project_teams = ProjectTeam.objects.filter(project_code=project_code)
    else:
        project_teams = ProjectTeam.objects.filter(allocated_hours__gt=0)
 
    data = []
 
    for team in project_teams:
        employee_code = team.employee_code.employee_code
        current_project_code = team.project_code.project_code
 
        alloc_obj = ProjectTeamAllocation.objects.filter(
            employee_code__employee_code=employee_code,
            project_code=current_project_code
        ).first()
 
        serializer = ProjectTeamSerializer(team)
        team_data = serializer.data
 
        # Adjust end_date for internal project
        project_obj = get_object_or_404(Project, project_code=current_project_code)
        team_data['end_date'] = (
            project_obj.to_date if current_project_code == 'RB001' else team.end_date
        )
 
        task_id = team.task.task_code if team.task else None
 
        worked_hours_qs = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=current_project_code,
            task_description_id=task_id,
            status='approved'
        ).aggregate(
            total=Coalesce(Sum('worked_hours'), Value(timedelta()))
        )
 
        total_worked = worked_hours_qs['total'] or timedelta()
 
        if total_worked:
            hours, remainder = divmod(total_worked.total_seconds(), 3600)
            minutes = remainder // 60
            team_data['worked_hours'] = f"{int(hours):02}:{int(minutes):02}"
        else:
            team_data['worked_hours'] = "00:00"
 
        # === Balance Hours (Approved + Open) ===
        approved_timesheets = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=current_project_code,
            task_description_id=task_id,
            status='approved'
        )
 
        open_timesheets = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            project_code__project_code=current_project_code,
            task_description_id=task_id,
            status='open'
        )
 
        approved_seconds = sum(
            ts.worked_hours.total_seconds()
            for ts in approved_timesheets
            if ts.worked_hours
        )
 
        open_seconds = sum(
            ts.worked_hours.total_seconds()
            for ts in open_timesheets
            if ts.worked_hours
        )
 
        total_seconds = approved_seconds + open_seconds
        worked_hours_in_hours = total_seconds / 3600
 
        allocated_hours = team.allocated_hours or 0
        team_data['balance_hours'] = round(
            allocated_hours - worked_hours_in_hours, 2
        )
 
        data.append(team_data)
 
    return Response(data, status=status.HTTP_200_OK)
#delete phasealloaction
class PhaseAllocationDeleteView(generics.DestroyAPIView):
    queryset = PhaseAllocation.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if timesheet entries exist for this phase allocation
        timesheet_entries_exist = EmployeeTimesheet.objects.filter(
            task_description=instance.task,  # Matches task in PhaseAllocation
            project_code=instance.project_code  # Matches project_code in PhaseAllocation
        ).exists()

        if timesheet_entries_exist:
            return Response(
                {"error": "Cannot delete this phase allocation. Timesheet entries exist for this phase."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #  Check if any ProjectTeam entries exist for this task and project_code
        project_team_exists = ProjectTeam.objects.filter(
            task=instance.task,  # Matches task in PhaseAllocation
            project_code=instance.project_code  # Matches project_code in PhaseAllocation
        ).exists()

        if project_team_exists:
            return Response(
                {"error": "Cannot delete this phase allocation. Project team members are assigned to this phase."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If no timesheet entries, proceed with deletion
        self.perform_destroy(instance)
        return Response({"message": "Phase allocation deleted successfully."}, status=status.HTTP_200_OK)

# # Get Phase Allocations by Project Code
class GetPhaseAllocationsByProjectView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "project_code",
                openapi.IN_QUERY,
                description="Filter phase allocations by project_code",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: PhaseAllocationSerializer(many=True)},
        operation_description="Retrieve phase allocations for a specific project"
    )
    def get(self, request, *args, **kwargs):
        project_code = request.GET.get("project_code")
        if not project_code:
            return Response({"error": "Project code is required"}, status=status.HTTP_400_BAD_REQUEST)

        allocations = PhaseAllocation.objects.select_related("task", "project_code").filter(project_code__project_code=project_code)

        return Response(PhaseAllocationSerializer(allocations, many=True).data, status=status.HTTP_200_OK)


#  GET API - List All Phase Allocations
class PhaseAllocationListView(generics.ListAPIView):
    serializer_class = PhaseAllocationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # All PhaseAllocation objects, but filtering logic is handled in serializer
        employee_code = self.request.query_params.get("employee_code", None)
        if employee_code:
            self.request.employee_code = employee_code  # Store in request for context
        return PhaseAllocation.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["employee_code"] = getattr(self.request, "employee_code", None)
        return context

#create single phaseallocation
class PhaseAllocationCreateView(generics.CreateAPIView):
    queryset = PhaseAllocation.objects.all()
    serializer_class = PhaseAllocationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        task_code = request.data.get("task")
        project_code = request.data.get("project_code")

        #  Validate Task
        try:
            task = ProjectTasks.objects.get(task_code=task_code)
        except ProjectTasks.DoesNotExist:
            return Response({"error": f"Task with task_code '{task_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

        #  Validate Project
        try:
            project = Project.objects.get(project_code=project_code)
        except Project.DoesNotExist:
            return Response({"error": f"Project with code '{project_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

        #  Check if PhaseAllocation Already Exists
        existing_allocation = PhaseAllocation.objects.filter(task=task, project_code=project).first()
        if existing_allocation:
            return Response({"error": "Phase Allocation for this task and project already exists.", 
                             "existing_data": PhaseAllocationSerializer(existing_allocation).data}, 
                            status=status.HTTP_400_BAD_REQUEST)

        #  Create a New Phase Allocation
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, project_code=project)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# #bulk craete phase allocation
class PhaseAllocationBulkCreateView(generics.CreateAPIView):
    queryset = PhaseAllocation.objects.all()
    serializer_class = PhaseAllocationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Bulk create Phase Allocations",
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'task': openapi.Schema(type=openapi.TYPE_STRING),
                    'project_code': openapi.Schema(type=openapi.TYPE_STRING),
                    'budgeted_hours': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'start_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    'end_date':openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE)
                }
            ),
        ),
        responses={201: "Phase Allocations created successfully.", 400: "Bad Request - Validation error."}
    )
    def post(self, request, *args, **kwargs):
        data_list = request.data

        if not isinstance(data_list, list):
            return Response({"error": "Request body must be a list of objects."}, status=status.HTTP_400_BAD_REQUEST)

        # Check for duplicate (task, project_code) in request body
        task_project_pairs = [(item.get("task"), item.get("project_code")) for item in data_list]
        duplicates = [pair for pair, count in Counter(task_project_pairs).items() if count > 1]
        if duplicates:
            formatted = [f"task '{t}' with project_code '{p}'" for t, p in duplicates]
            return Response({"error": f"Duplicate phase record not allowed: {formatted}"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Group new hours by project_code
        new_hours_by_project = defaultdict(int)
        for item in data_list:
            new_hours_by_project[item["project_code"]] += item.get("budgeted_hours", 0)

        # Validate budgeted hours per project
        for project_code, new_hours in new_hours_by_project.items():
            try:
                project = Project.objects.get(project_code=project_code)
            except Project.DoesNotExist:
                return Response({"error": f"Project with code '{project_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

            existing_hours = PhaseAllocation.objects.filter(project_code=project).aggregate(
                total=Coalesce(Sum("budgeted_hours"), Value(0))
            )["total"]

            if existing_hours + new_hours > project.budgeted_hours:
                return Response({
                    "error": (
                        f"Total budgeted hours ({existing_hours + new_hours}) exceed "
                        f"project budgeted hours ({project.budgeted_hours}) for project_code '{project_code}'."
                    )
                }, status=status.HTTP_400_BAD_REQUEST)

        # Proceed to creation
        created_allocations = []

        for data in data_list:
            task_code = data.get("task")
            project_code = data.get("project_code")
            budgeted_hours = data.get("budgeted_hours")

            # Validate task
            try:
                task = ProjectTasks.objects.get(task_code=task_code)
            except ProjectTasks.DoesNotExist:
                return Response({"error": f"Task with task_code '{task_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate project
            try:
                project = Project.objects.get(project_code=project_code)
            except Project.DoesNotExist:
                return Response({"error": f"Project with code '{project_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

            # Check for existing allocation
            if PhaseAllocation.objects.filter(task=task, project_code=project).exists():
                return Response({"error": f"Phase Allocation for task {task_code} and project {project_code} already exists."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create the allocation
            phase_allocation = PhaseAllocation.objects.create(
                task=task,
                project_code=project,
                budgeted_hours=budgeted_hours,
                allocated_hours=0,  
                start_date=data.get("start_date"),
                end_date=data.get("end_date")
            )

            created_allocations.append(phase_allocation)

        return Response({
            "message": "Phase Allocation created successfully.",
            "data": PhaseAllocationSerializer(created_allocations, many=True).data
        }, status=status.HTTP_201_CREATED)


# #update bulk phasealloaction
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def bulk_update_phase_allocations(request):
    updates = request.data

    if not isinstance(updates, list):
        return Response({"error": "Expected a list of objects."}, status=status.HTTP_400_BAD_REQUEST)

    phase_ids = [u.get("id") for u in updates]
    duplicate_ids = {i for i in phase_ids if phase_ids.count(i) > 1}
    if duplicate_ids:
        return Response({"error": "Duplicate phase entries are not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    task_project_pairs = [(u["task"], u["project_code"]) for u in updates]
    duplicates = {pair for pair in task_project_pairs if task_project_pairs.count(pair) > 1}
    if duplicates:
        return Response({
            "error": f"Duplicate tasks for same project found in request: {duplicates}"
        }, status=status.HTTP_400_BAD_REQUEST)

    project_update_totals = defaultdict(int)
    project_existing_totals = {}

    for update in updates:
        phase_id = update.get("id")
        project_code = update.get("project_code")
        budgeted_hours = update.get("budgeted_hours")

        try:
            project = Project.objects.get(project_code=project_code)
        except Project.DoesNotExist:
            return Response({"error": f"Project '{project_code}' not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            PhaseAllocation.objects.get(id=phase_id)
        except PhaseAllocation.DoesNotExist:
            return Response({"error": f"Phase cannot be updated once created."}, status=status.HTTP_400_BAD_REQUEST)

        if project_code not in project_existing_totals:
            existing_total = PhaseAllocation.objects.filter(project_code=project).exclude(id__in=phase_ids).aggregate(
                total=Coalesce(Sum("budgeted_hours"), Value(0))
            )["total"]
            project_existing_totals[project_code] = existing_total

        project_update_totals[project_code] += budgeted_hours

    for project_code, update_total in project_update_totals.items():
        project = Project.objects.get(project_code=project_code)
        total = update_total + project_existing_totals[project_code]
        if total > project.budgeted_hours:
            return Response({
                "error": f"Total budgeted hours ({total}) exceed project budgeted hours ({project.budgeted_hours}) for project_code '{project_code}'."
            }, status=status.HTTP_400_BAD_REQUEST)

    updated_data = []
    errors = []

    for update in updates:
        phase_id = update.get("id")
        task_code = update.get("task")
        project_code = update.get("project_code")
        budgeted_hours = update.get("budgeted_hours")
        start_date = update.get("start_date")
        end_date = update.get("end_date")

        try:
            task = ProjectTasks.objects.get(task_code=task_code)
        except ProjectTasks.DoesNotExist:
            errors.append({"id": phase_id, "error": f"Task '{task_code}' not found."})
            continue

        task_group = task.task_group  

        try:
            phase_allocation = PhaseAllocation.objects.get(id=phase_id)
        except PhaseAllocation.DoesNotExist:
            errors.append({"id": phase_id, "error": "Phase cannot be updated once created"})
            continue

        duplicate_phase = PhaseAllocation.objects.filter(
            project_code__project_code=project_code,
            task__task_code=task_code
        ).exclude(id=phase_id).exists()

        if duplicate_phase:
            errors.append({
                "id": phase_id,
                "error": f"Task '{task_code}' already exists for project '{project_code}'."
            })
            continue

        if str(phase_allocation.task.task_code) != str(task_code):
            timesheet_exists = EmployeeTimesheet.objects.filter(
                project_code=project_code,
                task_description=phase_allocation.task.task_code
            ).exists()

            if timesheet_exists:
                errors.append({
                    "id": phase_id,
                    "error": f"Cannot change phase from '{phase_allocation.task.task_group}' to '{task_group}' because timesheet entries exist."
                })
                continue

            phase_allocation.task = task

        if budgeted_hours < phase_allocation.allocated_hours:
            errors.append({
                "id": phase_id,
                "error": f"Cannot decrease budgeted_hours to {budgeted_hours} because allocated_hours is already {phase_allocation.allocated_hours}."
            })
            continue

        phase_allocation.budgeted_hours = budgeted_hours
        phase_allocation.start_date = start_date
        phase_allocation.end_date = end_date
        phase_allocation.save()

        updated_data.append({
            "id": phase_allocation.id,
            "task": phase_allocation.task.task_code,
            "project_code": project_code,
            "budgeted_hours": budgeted_hours,
            "allocated_hours": phase_allocation.allocated_hours,
            "start_date": phase_allocation.start_date,
            "end_date": phase_allocation.end_date
        })

    if errors:
        return Response({"updated": updated_data, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "message": "Successfully updated Phase Allocations.",
        "updated_data": updated_data
    }, status=status.HTTP_200_OK)

#get pmo-report based on dates
def format_duration(total_seconds):
    total_minutes = int(total_seconds // 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
class PMOReportAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get PMO report between dates for a project",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['start_date', 'end_date', 'project_code'],
            properties={
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'project_code': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: 'PMO Report'},
    )
    def post(self, request):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        project_code = request.data.get("project_code")

        timesheets = EmployeeTimesheet.objects.filter(
            date__range=[start_date, end_date],
            project_code__project_code=project_code
        ).select_related("employee_code", "task_description", "project_code")

        report = {}
        for entry in timesheets:
            emp_code = entry.employee_code.employee_code
            emp_name = entry.employee_code.name
            log_date = entry.date.strftime("%Y-%m-%d")
            project_description = entry.project_code.project_description if entry.project_code else ""
            


            if emp_code not in report:
                report[emp_code] = {
                    "employee_code": emp_code,
                    "employee_name": emp_name,
                    "log": {}
                }

            if log_date not in report[emp_code]["log"]:
                report[emp_code]["log"][log_date] = {
                    # "total_hours": "00:00",
                    "details": []
                }
            def format_worked_hours(td):
                total_seconds = int(td.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours:02}:{minutes:02}"

            # Build entry
            detail = {
                "date": log_date,
                "emp_code": emp_code,
                "emp_name": emp_name,
                "project_name": project_description,
                "phase": entry.task_description.task_group if entry.task_description else "",
                "task_description": entry.new_description,
                # "worked_hours": str(entry.worked_hours),
                "worked_hours": format_worked_hours(entry.worked_hours),
                "remarks": entry.remarks,
                "status": entry.status
            }


            report[emp_code]["log"][log_date]["details"].append(detail)

        # Total & average
        for emp in report.values():
            total_seconds = 0
            days = 0
            for log in emp["log"].values():
                # Get all statuses for that date
                statuses = [d["status"].lower() for d in log["details"]]
                # Sum worked_hours where status is 'approved' or 'open'
                hours = sum([
                    int(d["worked_hours"].split(":")[0]) * 3600 +
                    int(d["worked_hours"].split(":")[1]) * 60
                    for d in log["details"] if d["status"].lower() in ("approved", "open")
                ])

                total_seconds += hours
                if hours > 0:
                    days += 1
                log["total_hours"] = "{:02}:{:02}".format(hours // 3600, (hours % 3600) // 60)
                                # === Per-Date Allocation Percent ===
                log_date = list(log["details"])[0]["date"]  # string yyyy-mm-dd
                log_dt = datetime.strptime(log_date, "%Y-%m-%d").date()

                allocation_percent = 0

                alloc_obj = ProjectTeamAllocation.objects.filter(
                    employee_code__employee_code=emp["employee_code"],
                    project_code__project_code=project_code
                ).first()

                if alloc_obj:
                    valid_history = [
                        h for h in alloc_obj.history.all()
                        if h.allocation_start_date <= log_dt <= h.allocation_end_date
                    ]

                    valid_history.sort(key=lambda h: h.updated_at, reverse=True)

                    if valid_history:
                        allocation_percent = valid_history[0].allocation_percent

                log["allocation_percent"] = allocation_percent


              # Set status_flag based on details for each DATE (log)
                if all(status == "approved" for status in statuses):
                    log["status_flag"] = "Approved"
                elif all(status == "rejected" for status in statuses):
                    log["status_flag"] = "Rejected"
                elif any(status == "open" for status in statuses):
                    log["status_flag"] = "Open"
                else:
                    log["status_flag"] = "Approved"
            emp["total"] = "{:02}:{:02}".format(total_seconds // 3600, (total_seconds % 3600) // 60)
            avg_seconds = total_seconds // days if days else 0
            emp["average"] = "{:02}:{:02}".format(avg_seconds // 3600, (avg_seconds % 3600) // 60)

        return Response(list(report.values()), status=status.HTTP_200_OK)


# assign allocation
def dates_overlap(start1, end1, start2, end2):
    """Check if two date ranges overlap."""
    return start1 <= end2 and start2 <= end1

@swagger_auto_schema(
    method='post',
    operation_description="Assign allocation % for multiple employees on projects.",
    request_body=openapi.Schema(
        type=openapi.TYPE_ARRAY,
        items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
            'employee_code': openapi.Schema(type=openapi.TYPE_STRING),
            'project_code': openapi.Schema(type=openapi.TYPE_STRING),
            'allocation_percent': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
        })),
    responses={
        201: "Allocations created/updated successfully.",
        400: "Bad Request - Validation error."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def assign_allocation_percent(request):
    try:
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of allocations."}, status=400)

        today = date.today()
        response_data = []
        temp_alloc_map = defaultdict(dict)

        # Step 1: Prepare incoming data
        for item in request.data:
            emp = item.get("employee_code")
            proj = item.get("project_code")
            alloc = item.get("allocation_percent")
            if not all([emp, proj, alloc is not None]):
                return Response({"error": f"Missing fields in: {item}"}, status=400)
            temp_alloc_map[emp][proj] = float(alloc)

        # Step 2: Validate allocations
        for emp_code, project_allocs in temp_alloc_map.items():
            employee = Employee.objects.get(employee_code=emp_code)

            for proj_code, alloc_percent in project_allocs.items():
                project = Project.objects.get(project_code=proj_code)
                project_teams = ProjectTeam.objects.filter(
                    project_code=project,
                    employee_code=employee
                )

                if not project_teams.exists():
                    return Response({
                        "error": f"No ProjectTeam assignment found for {emp_code} in {proj_code}"
                    }, status=400)

                # Use the first team record or any logic you want (assuming one active team per project)
                project_team = project_teams.first()
                proj_start = project_team.start_date
                proj_end = project_team.end_date or proj_start

                # Fetch all allocations for this employee excluding current project
                existing_allocs = ProjectTeamAllocation.objects.filter(
                    employee_code=employee
                ).exclude(project_code=project).select_related('project_code')

                # Keep only active/future allocations
                active_existing_allocs = []
                for existing in existing_allocs:
                    existing_teams = ProjectTeam.objects.filter(
                        project_code=existing.project_code,
                        employee_code=employee
                    )
                    for existing_team in existing_teams:
                        existing_start = existing_team.start_date
                        existing_end = existing_team.end_date or existing_start

                        if existing_end < today:
                            continue
                        active_existing_allocs.append((existing, existing_team))

                # Step 2a: Check overlaps
                for existing, existing_team in active_existing_allocs:
                    existing_start = existing_team.start_date
                    existing_end = existing_team.end_date or existing_team.start_date

                    if dates_overlap(proj_start, proj_end, existing_start, existing_end):
                        total_in_overlap = existing.allocation_percent + float(alloc_percent)
                        if total_in_overlap > 100:
                            return Response({
                                "error": f"Cannot assign {alloc_percent}% for {emp_code} in {proj_code}. "
                                         f"Overlaps with {existing.project_code.project_code} "
                                         f"({existing.allocation_percent}%). "
                                         f"Total in overlap period = {total_in_overlap}% (limit 100%)."
                            }, status=400)

        # Step 3: Save validated allocations
        for emp_code, project_allocs in temp_alloc_map.items():
            employee = Employee.objects.get(employee_code=emp_code)

            for proj_code, alloc_percent in project_allocs.items():
                project = Project.objects.get(project_code=proj_code)

                # Calculate total allocation for active projects excluding current project
                total_allocation = 0.0
                existing_allocs = ProjectTeamAllocation.objects.filter(
                    employee_code=employee
                ).exclude(project_code=project).select_related('project_code')

                for existing in existing_allocs:
                    existing_teams = ProjectTeam.objects.filter(
                        project_code=existing.project_code,
                        employee_code=employee
                    )
                    for existing_team in existing_teams:
                        existing_end = existing_team.end_date or existing_team.start_date
                        if existing_end >= today:
                            total_allocation += existing.allocation_percent

                new_total = total_allocation + float(alloc_percent)
                if new_total > 100:
                    return Response({
                        "error": f"Cannot assign {alloc_percent}% for {emp_code} in {proj_code}. "
                                 f"Total allocation would become {new_total}%, exceeding the 100% limit."
                    }, status=400)

                # Save allocation
                allocation_obj, created = ProjectTeamAllocation.objects.update_or_create(
                    employee_code=employee,
                    project_code=project,
                    defaults={'allocation_percent': alloc_percent}
                )

                response_data.append({
                    "employee_code": emp_code,
                    "project_code": proj_code,
                    "allocation_percent": alloc_percent,
                    "total_allocation_percent": new_total,
                    "action": "created" if created else "updated"
                })

        return Response({
            "message": "Allocations processed successfully.",
            "data": response_data
        }, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

# @receiver(post_delete, sender=ProjectTeam)
# def delete_allocation_on_team_delete(sender, instance, **kwargs):
#     ProjectTeamAllocation.objects.filter(
#         employee_code=instance.employee_code,
#         project_code=instance.project_code
#     ).delete()
@receiver(post_delete, sender=ProjectTeam)
def delete_allocation_on_team_delete(sender, instance, **kwargs):
    other_team_exists = ProjectTeam.objects.filter(
        employee_code=instance.employee_code,
        project_code=instance.project_code
    ).exists()

    if not other_team_exists:
        ProjectTeamAllocation.objects.filter(
            employee_code=instance.employee_code,
            project_code=instance.project_code
        ).delete()

# employee availability
availability_param = openapi.Parameter(
    'availability_period',
    openapi.IN_QUERY,
    description="Number of days ahead to check employee availability",
    type=openapi.TYPE_INTEGER,
    default=30,
    required=False
)

@swagger_auto_schema(
    method='get',
    operation_summary="Employee Availability Report",
    operation_description="Get availability report of employees for the next X days.",
    manual_parameters=[availability_param],
    responses={200: "Availability data retrieved successfully."}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_availability_report(request):
    days = int(request.query_params.get('availability_period', 30))
    today = timezone.now().date()
    period_end = today + timedelta(days=days)
    internal_project_code = "RB001"

    final_data = []
    emp_end_map = defaultdict(lambda: defaultdict(float))
    
    # NEW: Use a single comprehensive employee map
    employee_map = {}  # {employee_code: {name, primary_skill, secondary_skill, department}}

    # Step 1: Pre-fetch ALL active employees with their details
    all_active_employees = Employee.objects.filter(status='active').values(
        'employee_code', 'name', 'primary_skill', 'secondary_skill', 'department'
    )
    
    # Populate employee map with actual data from database
    for emp in all_active_employees:
        employee_map[emp['employee_code']] = {
            'name': emp['name'],
            'primary_skill': emp['primary_skill'] if emp['primary_skill'] else [],
            'secondary_skill': emp['secondary_skill'] if emp['secondary_skill'] else [],
            'department': emp['department'] if emp['department'] else 'Not Specified'
        }

    # Step 2: Build availability baseline (today) and future increments
    all_allocations = (
        ProjectTeamAllocation.objects
        .exclude(project_code__project_code=internal_project_code)
        .select_related('employee_code', 'project_code')
        .filter(employee_code__status='active')
    )

    todays_done = set()

    for alloc in all_allocations:
        emp = alloc.employee_code
        emp_code = emp.employee_code
        allocation_percent = float(alloc.allocation_percent)

        latest_team = (
            ProjectTeam.objects
            .filter(employee_code=emp, project_code=alloc.project_code)
            .order_by('-end_date')
            .first()
        )
        if not latest_team:
            continue

        start_date = latest_team.start_date
        end_date = latest_team.end_date

        # A) If project overlaps today
        if start_date <= today <= end_date and emp_code not in todays_done:
            active_projects_qs = (
                ProjectTeam.objects
                .filter(
                    employee_code=emp,
                    start_date__lte=today,
                    end_date__gte=today
                )
                .values('project_code')
            )
            total_alloc_today = (
                ProjectTeamAllocation.objects
                .exclude(project_code__project_code=internal_project_code)
                .filter(
                    employee_code=emp,
                    project_code__in=Subquery(active_projects_qs)
                )
                .aggregate(total=Coalesce(Sum('allocation_percent'), Value(0.0), output_field=FloatField()))['total'] or 0.0
            )

            available_today = max(0.0, 100.0 - float(total_alloc_today))
            emp_end_map[emp_code][today] = available_today
            todays_done.add(emp_code)

        # B) If project ends today or in the future
        if end_date >= today:
            availability_date = end_date + timedelta(days=1)
            if availability_date <= period_end:
                emp_end_map[emp_code][availability_date] += allocation_percent

    # Step 3: Employees whose all projects ended before today or have no projects
    for emp_code, emp_data in employee_map.items():
        if emp_code not in emp_end_map:
            # Check if employee has any projects
            emp_projects = ProjectTeam.objects.filter(
                employee_code__employee_code=emp_code
            ).exclude(project_code__project_code=internal_project_code)

            if not emp_projects.exists() or emp_projects.aggregate(max_end=Max('end_date'))['max_end'] < today:
                # Employee has no projects or all ended before today → 100% available today
                emp_end_map[emp_code][today] = 100.0

    # Step 4: Build cumulative timeline with imported employee data
    for emp_code, date_map in emp_end_map.items():
        running_total = 0.0
        for avail_date in sorted(date_map):
            running_total += float(date_map[avail_date])
            if running_total > 100.0:
                running_total = 100.0

            if avail_date <= period_end:
                emp_data = employee_map.get(emp_code, {})
                final_data.append({
                    "employee_code": emp_code,
                    "employee_name": emp_data.get('name', ''),
                    "project_code": internal_project_code,
                    "project_name": "Internal Project",
                    "allocation_percent": round(running_total, 2),
                    "availability_date": avail_date.strftime('%d-%b-%y'),
                    "total_allocation_percent": 100,
                    # Imported fields from Employee model
                    "primary_skill": emp_data.get('primary_skill', []),
                    "secondary_skill": emp_data.get('secondary_skill', []),
                    "department": emp_data.get('department', 'Not Specified')
                })

    # Step 5: Pick one row per employee
    employee_availability_map = {}
    for entry in final_data:
        emp_code = entry["employee_code"]
        avail_date = datetime.strptime(entry["availability_date"], '%d-%b-%y').date()
        alloc_percent = float(entry["allocation_percent"])

        if emp_code not in employee_availability_map:
            employee_availability_map[emp_code] = {**entry, "_date": avail_date}
        else:
            existing = employee_availability_map[emp_code]
            existing_date = existing["_date"]
            existing_alloc = float(existing["allocation_percent"])

            if avail_date == today:
                employee_availability_map[emp_code] = {**entry, "_date": avail_date}
            elif alloc_percent > existing_alloc:
                employee_availability_map[emp_code] = {**entry, "_date": avail_date}
            elif alloc_percent == existing_alloc and avail_date < existing_date:
                employee_availability_map[emp_code] = {**entry, "_date": avail_date}

    final_filtered_data = [
        {k: v for k, v in entry.items() if k != "_date"}
        for entry in employee_availability_map.values()
        if float(entry["allocation_percent"]) > 0.0
    ]

    return Response({
        "message": f"Employee availability report for next {days} days.",
        "availability_period": f"{days} Days",
        "data": final_filtered_data
    })

# employee details with project code
@swagger_auto_schema(
    method='get',
    operation_description="Get all employee details for a specific project including allocation and worked hours",
    manual_parameters=[
        openapi.Parameter(
            'project_code',
            openapi.IN_PATH,
            description="Project code",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Employee details retrieved successfully.",
            schema=ProjectEmployeeDetailsSerializer(many=True)
        ),
        404: openapi.Response(description="Project not found."),
        400: openapi.Response(description="Bad request.")
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_employee_details(request, project_code):
    """
    Get all employee details for a specific project.
    Output: Employee Code, Employee Name, Start Date, End Date, Allocation %, Allocated Hrs, Worked Hrs
    """
    try:
        project = Project.objects.get(project_code=project_code)
    except Project.DoesNotExist:
        return Response(
            {"error": f"Project with code '{project_code}' not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get distinct employees for this project
    distinct_employees = ProjectTeam.objects.filter(
        project_code__project_code=project_code
    ).values('employee_code').distinct()

    final_data = []
    
    for emp in distinct_employees:
        emp_id = emp['employee_code']
        
        # Get ALL phases for this specific employee
        employee_phases = ProjectTeam.objects.filter(
            project_code__project_code=project_code,
            employee_code_id=emp_id
        ).select_related('employee_code')
        
        if employee_phases.exists():
            # Calculate date range for THIS employee across ALL their phases
            date_range = employee_phases.aggregate(
                overall_start_date=Min('start_date'),
                overall_end_date=Max('end_date')
            )
            
            # Calculate total allocated hours for THIS employee
            total_hours = employee_phases.aggregate(
                total_allocated=Sum('allocated_hours')
            )['total_allocated'] or 0
            
            # Get employee details from first phase
            first_phase = employee_phases.first()
            
            employee_data = {
                'employee_code': first_phase.employee_code.employee_code,
                'employee_name': first_phase.employee_code.name,
                'project_code': project_code,
                'allocated_hours': total_hours,
                'start_date': date_range['overall_start_date'],  # Min across all phases
                'end_date': date_range['overall_end_date']       # Max across all phases
            }
            
            final_data.append(employee_data)

    if not final_data:
        return Response({
            "message": f"No employees found for project {project_code}",
            "data": []
        }, status=status.HTTP_200_OK)

    serializer = ProjectEmployeeDetailsSerializer(final_data, many=True)

    return Response({
        "message": f"Employee details retrieved successfully for project {project_code}",
        "project_code": project_code,
        "project_description": project.project_description,
        "data": serializer.data
    }, status=status.HTTP_200_OK)



# Swagger schema for POST request
phase_allocation_request_schema = openapi.Schema(
    type=openapi.TYPE_ARRAY,
    items=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "projectCode": openapi.Schema(type=openapi.TYPE_STRING, description="Project code"),
            "taskCode": openapi.Schema(type=openapi.TYPE_STRING, description="Task/Phase code (task_code)"),
            "allocationPercent": openapi.Schema(type=openapi.TYPE_INTEGER, description="Allocation percent (0-100)"),
            "allocationStartDate": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="Start date (YYYY-MM-DD)"),
            "allocationEndDate": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="End date (YYYY-MM-DD)"),
        }
    ),
    description="List of phase-wise allocations"
)


# def dates_overlap(start1, end1, start2, end2):
#     """Return True if two date ranges overlap (inclusive)."""
#     return start1 <= end2 and start2 <= end1

def daterange(start, end):
    for i in range((end - start).days + 1):
        yield start + timedelta(days=i)


def build_daily_allocation(employee):
    daily = defaultdict(lambda: defaultdict(float))
    hist_qs = PhaseTeamAllocationHistory.objects.filter(
        allocation__employee=employee
    ).order_by("id")

    for row in hist_qs:
        pid = str(row.allocation.project.project_code).strip()
        tid = str(row.allocation.task.task_code).strip()
        pct = float(row.allocation_percent)

        for d in daterange(row.allocation_start_date, row.allocation_end_date):
            daily[d][(pid, tid)] = pct
    curr = PhaseTeamAllocation.objects.filter(employee=employee)
    for row in curr:
        pid = str(row.project.project_code).strip()
        tid = str(row.task.task_code).strip()
        pct = float(row.allocation_percent)

        for d in daterange(row.allocation_start_date, row.allocation_end_date):
            daily[d][(pid, tid)] = pct

    return daily

def _create_allocation_segment(employee, project, task, start_date, end_date, percent, updated_by_email):
    """
    FIX: Because PhaseTeamAllocation has unique (employee, project, task),
    we must UPDATE instead of CREATE if one already exists.
    """

    obj, created = PhaseTeamAllocation.objects.update_or_create(
        employee=employee,
        project=project,
        task=task,
        defaults={
            "allocation_start_date": start_date,
            "allocation_end_date": end_date,
            "allocation_percent": percent
        }
    )

    PhaseTeamAllocationHistory.objects.create(
        allocation=obj,
        allocation_percent=percent,
        allocation_start_date=start_date,
        allocation_end_date=end_date,
        updated_by=updated_by_email
    )
    return obj



# ----------------- Endpoint -----------------
@swagger_auto_schema(
    method='get',
    operation_summary="Get all projects for an employee (phase-wise)",
    operation_description="Returns a list of projects assigned to the employee with phase-wise allocations and history.",
    responses={
        200: openapi.Response(
            description="List of employee projects with phases",
            examples={
                "application/json": [
                    {
                        "projectName": "Internal Project",
                        "projectCode": "RB001",
                        "managerName": "Kiran Kumar",
                        "startDate": "2025-09-02",
                        "endDate": "2125-12-31",
                        "phases": [
                            {
                                "taskCode": "DEV",
                                "PhaseName": "Development",
                                "PhaseStartDate":"2025-01-01",
                                "phaseEndDate":"2025-01-2026",
                                "allocationPercent": 50,
                                "allocationStartDate": "2025-09-01",
                                "allocationEndDate": "2025-12-31",
                                "allocationHistory": [
                                    {
                                        "allocationPercent": 60,
                                        "fromDate": "2025-07-01",
                                        "toDate": "2025-08-31",
                                        "timestamp": "2025-08-31T12:00:00Z",
                                        "updatedBy":"user@example.com"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ),
        404: "No projects found for employee"
    }
)
@swagger_auto_schema(
    method="post",
    operation_summary="Add or update phase-wise allocation",
    operation_description="Create or update allocation percent for an employee for a given project phase (task). Validates overlapping allocations do not exceed 100%.",
    request_body=phase_allocation_request_schema,
    responses={
        200: openapi.Response(
            description="Allocations created or updated successfully",
            examples={
                "application/json": {
                    "message": "Allocations processed successfully",
                    "updated": [
                        {
                            "projectCode": "QA4",
                            "taskCode": "DEV",
                            "allocationPercent": 50,
                            "message": "updated"
                        }
                    ]
                }
            }
        ),
        400: "Invalid input / Allocation exceeds 100%",
        404: "Project or task not found for employee"
    }
)
@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_projects(request, employee_code):
    overlapping_details = []

    try:
        if request.method == 'POST':
            data = request.data
            if isinstance(data, dict):
                data = [data]

            overlapping_details = []
            updated_allocations = []

            def _parse_date_safe(val):
                if not val:
                    return None
                return datetime.strptime(val, "%Y-%m-%d").date()

            with transaction.atomic():
                # --- EMPLOYEE CHECK ---
                employee = Employee.objects.filter(employee_code=employee_code).first()
                if not employee:
                    return Response({"error": f"Employee not found: {employee_code}"}, status=404)

                project_teams = ProjectTeam.objects.filter(employee_code=employee).select_related('project_code')
                if not project_teams.exists():
                    return Response({"message": f"No projects found for employee {employee_code}"}, status=status.HTTP_404_NOT_FOUND)

                project_codes = {pt.project_code.project_code for pt in project_teams}
                for item in data:
                    if item["projectCode"] not in project_codes:
                        return Response({"error": f"Employee not assigned to this project {item['projectCode']}"},
                                        status=400)
                incoming = []
                for item in data:
                    proj = Project.objects.filter(project_code=item["projectCode"]).first()
                    if not proj:
                        return Response({"error": f"Project not found: {item['projectCode']}"}, status=400)

                    task = ProjectTasks.objects.filter(task_code=item["taskCode"]).first()
                    if not task:
                        return Response({"error": f"Task not found: {item['taskCode']}"}, status=400)

                    phase = PhaseAllocation.objects.filter(project_code=proj, task=task).first()
                    if not phase:
                        return Response({"error": f"No phase for project {item['projectCode']} task {item['taskCode']}"}, status=400)

                    s = _parse_date_safe(item.get("allocationStartDate")) or phase.start_date
                    e = _parse_date_safe(item.get("allocationEndDate")) or phase.end_date

                    if s < phase.start_date or e > phase.end_date:
                        return Response({
                            "error": f"Allocation dates must lie inside phase for {item['projectCode']} {item['taskCode']}"
                        }, status=400)

                    inc = {
                        "project": proj,
                        "task": task,
                        "projectCode": str(proj.project_code).strip(),
                        "taskCode": str(task.task_code).strip(),
                        "start": s,
                        "end": e,
                        "percent": float(item["allocationPercent"]),
                        "phase_start": phase.start_date,
                        "phase_end": phase.end_date,
                        "phase_name": task.task_group
                    }
                    incoming.append(inc)
                    overlapping_details.append({
                        "projectCode": proj.project_code,
                        "taskCode": task.task_code,
                        "phase_name": task.task_group,
                        "phase_start_date": str(phase.start_date),
                        "phase_end_date": str(phase.end_date),
                        "allocation_start_date": str(s),
                        "allocation_end_date": str(e),
                        "allocation_percent": float(item["allocationPercent"])
                    })

                existing_daily = build_daily_allocation(employee)
                violation_start = None
                violation_end = None

                for inc in incoming:  
                    pid = str(inc["projectCode"]).strip()
                    tid = str(inc["taskCode"]).strip()
                    pct = float(inc["percent"])
                    if pct == 0:
                        continue

                    for d in daterange(inc["start"], inc["end"]):
                        other_total = sum(
                            v for (p, t), v in existing_daily[d].items()
                            if not (p == pid and t == tid)
                        )
                        if other_total + pct > 100:
                            if violation_start is None or d < violation_start:
                                violation_start = d
                            if violation_end is None or d > violation_end:
                                violation_end = d
                        existing_daily[d][(pid, tid)] = pct 


                if violation_start is not None:
                    trimmed_details = []
                    seen = set()
                    
                    # ONLY show incoming allocations that overlap violation window
                    # + existing allocations that actually cause >100% conflict
                    for a in incoming:
                        if a["percent"] == 0:  
                            continue
                        overlap_start = max(a["start"], violation_start)
                        overlap_end = min(a["end"], violation_end)
                        if overlap_start <= overlap_end:
                            unique_key = (a["projectCode"], a["taskCode"])
                            if unique_key not in seen:
                                seen.add(unique_key)
                                
                                project_team = ProjectTeam.objects.filter(
                                    employee_code=employee, 
                                    project_code=a["project"], 
                                    task=a["task"]
                                ).first()
                                phase_start = project_team.start_date if project_team else a["phase_start"]
                                phase_end = project_team.end_date if project_team else a["phase_end"]
                                
                                trimmed_details.append({
                                    "projectCode": a["projectCode"],
                                    "taskCode": a["taskCode"],
                                    "phase_name": a["phase_name"],
                                    "phase_start_date": str(phase_start),
                                    "phase_end_date": str(phase_end),
                                    "allocation_start_date": str(overlap_start),
                                    "allocation_end_date": str(overlap_end),
                                    "allocation_percent": a["percent"]  # ALWAYS use incoming percent ✓
                                })
                    
                    # Add existing Pro2 75% (the actual conflict cause)
                    for day in daterange(violation_start, violation_end):
                        for (pid, tid), pct in existing_daily[day].items():
                            if pct > 0 and (pid, tid) not in seen:  # Only existing with actual %
                                seen.add((pid, tid))
                                project = Project.objects.filter(project_code=pid).first()
                                task_obj = ProjectTasks.objects.filter(task_code=tid).first()
                                phase = PhaseAllocation.objects.filter(project_code=project, task=task_obj).first() if project and task_obj else None
                                
                                trimmed_details.insert(0, {  # Add FIRST
                                    "projectCode": pid,
                                    "taskCode": tid,
                                    "phase_name": phase.task.task_group if phase and phase.task else "1 Prepare",
                                    "phase_start_date": str(phase.start_date) if phase else "2025-11-01",
                                    "phase_end_date": str(phase.end_date) if phase else "2026-01-30",
                                    "allocation_start_date": str(violation_start),
                                    "allocation_end_date": str(violation_end),
                                    "allocation_percent": pct  # Existing 75%
                                })
                                break  # Only need one existing per (project,task)
                    
                    return Response({
                        "error": "Allocation exceeds 100% within overlapping date range",
                        "details": trimmed_details
                    }, status=status.HTTP_400_BAD_REQUEST)



                    for d in daterange(inc["start"], inc["end"]):
                        existing_daily[d][(pid, tid)] = pct

                for inc in incoming:
                    proj = inc["project"]
                    task = inc["task"]
                    start = inc["start"]
                    end = inc["end"]
                    pct = inc["percent"]

                    overlapping_qs = PhaseTeamAllocation.objects.filter(
                        employee=employee,
                        project=proj,
                        task=task,
                        allocation_end_date__gte=start,
                        allocation_start_date__lte=end
                    ).order_by("allocation_start_date")

                    for old in overlapping_qs:
                        if old.allocation_start_date < start:
                            pre_start = old.allocation_start_date
                            pre_end = start - timedelta(days=1)
                            if pre_start <= pre_end:
                                _create_allocation_segment(employee, proj, task, pre_start, pre_end, float(old.allocation_percent), request.user.email)

                        if old.allocation_end_date > end:
                            post_start = end + timedelta(days=1)
                            post_end = old.allocation_end_date
                            if post_start <= post_end:
                                _create_allocation_segment(employee, proj, task, post_start, post_end, float(old.allocation_percent), request.user.email)

                    # if overlapping_qs.exists():
                    #     overlapping_qs.delete()

                    created_obj = _create_allocation_segment(employee, proj, task, start, end, pct, request.user.email)

                    updated_allocations.append({
                        "projectCode": inc["projectCode"],
                        "taskCode": inc["taskCode"],
                        "allocationPercent": pct,
                        "allocationStartDate": str(start),
                        "allocationEndDate": str(end),
                        "phaseStartDate": str(inc["phase_start"]),
                        "phaseEndDate": str(inc["phase_end"]),
                        "phase_name": inc["phase_name"],
                        "message": "updated"
                    })

            return Response({
                "message": "Phase-wise allocations processed successfully",
                "updated": updated_allocations,
                "overlapping_details": overlapping_details
            }, status=200)
        
        employee_obj = Employee.objects.filter(employee_code=employee_code).first()
        if not employee_obj:
            return Response({"message": f"No employee found: {employee_code}"}, status=404)

        project_teams = ProjectTeam.objects.filter(employee_code=employee_obj).select_related('project_code')
        if not project_teams.exists():
            return Response({"message": f"No projects found for employee {employee_code}"}, status=404)

        # Merge project date ranges
        merged_projects = {}
        for team in project_teams:
            pcode = team.project_code.project_code
            if pcode not in merged_projects:
                merged_projects[pcode] = {
                    "project": team.project_code,
                    "start_date": team.start_date,
                    "end_date": team.end_date
                }
            else:
                merged_projects[pcode]["start_date"] = min(merged_projects[pcode]["start_date"], team.start_date)
                merged_projects[pcode]["end_date"] = max(merged_projects[pcode]["end_date"], team.end_date)

        response_data = []
        for project_code, info in merged_projects.items():
            project = info["project"]

            # All tasks for this employee in this project
            project_tasks = ProjectTeam.objects.filter(project_code=project, employee_code=employee_obj).values_list('task', flat=True)

            project_phases = PhaseAllocation.objects.filter(project_code=project, task__in=project_tasks)

            phases = []
            for phase in project_phases:
                # Fetch all allocations for this employee/project/task
                allocations = PhaseTeamAllocation.objects.filter(
                    employee=employee_obj,
                    project=phase.project_code,
                    task=phase.task
                ).order_by('allocation_start_date')

                history_entries = []
                latest_alloc = None

                for alloc in allocations:
                    # Include history entries from each allocation
                    for h in alloc.history.all().order_by('-updated_at'):  
                        history_entries.append({
                            "allocationPercent": h.allocation_percent,
                            "fromDate": str(h.allocation_start_date),
                            "toDate": str(h.allocation_end_date),
                            "timestamp": h.updated_at.isoformat(),
                            "updatedBy": h.updated_by
                        })

                    # Keep track of latest allocation for main fields
                    latest_alloc = alloc

                if latest_alloc:
                    apct = latest_alloc.allocation_percent
                    astart = str(latest_alloc.allocation_start_date)
                    aend = str(latest_alloc.allocation_end_date)
                else:
                    apct = 0
                    astart = None
                    aend = None

                # Get phase start/end from ProjectTeam if exists
                team = ProjectTeam.objects.filter(project_code=project, employee_code=employee_obj, task=phase.task).first()
                phase_start = team.start_date if team else None
                phase_end = team.end_date if team else None

                phases.append({
                    "taskCode": phase.task.task_code,
                    "phaseName": phase.task.task_group or str(phase.task),
                    "phaseStartDate": str(phase_start) if phase_start else None,
                    "phaseEndDate": str(phase_end) if phase_end else None,
                    "allocationPercent": apct,
                    "allocationStartDate": astart,
                    "allocationEndDate": aend,
                    "allocationHistory": history_entries
                })

            response_data.append({
                "projectName": project.project_description,
                "projectCode": project.project_code,
                "managerName": project.project_manager,
                "startDate": str(project.from_date),
                "endDate": str(project.to_date),
                "phases": phases
            })

        return Response(response_data, status=200)

    except Exception as e:
        return Response({"error": str(e), "overlapping_details": overlapping_details}, status=500)

class MissedTimesheetSummaryAPI(APIView):
    """
    Returns missed timesheet summary grouped by Project and Employee.
    Uses the EXACT SAME LOGIC as the management command.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
 
    @swagger_auto_schema(
        operation_description="Get missed timesheet summary for one or more projects (only active ones).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'project_codes': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="Optional list of project codes to filter results"
                ),
            },
        ),
        responses={200: "List of missed timesheet summaries"},
    )
    def post(self, request):
 
        project_codes = request.data.get("project_codes", [])
        today = date.today()
        april_first = date(today.year, 4, 1)
 
        def get_last_friday(ref_date):
            days_since_friday = (ref_date.weekday() - 4) % 7
            return ref_date - timedelta(days=days_since_friday)
       
        if today < april_first:  # If current date is before April 1st
            april_first = date(today.year - 1, 4, 1)
 
        last_friday = today
 
        start_date, end_date = april_first, last_friday
 
        if start_date > end_date:
            return Response({"error": "Invalid date range"}, status=status.HTTP_400_BAD_REQUEST)
 
        # Weekdays only
        total_days = (end_date - start_date).days + 1
        date_list = [
            start_date + timedelta(days=i)
            for i in range(total_days)
            if (start_date + timedelta(days=i)).weekday() < 5
        ]
 
        employees = Employee.objects.filter(status="active")
 
        summary = []
 
        for emp in employees:
            project_teams = ProjectTeam.objects.filter(employee_code=emp)
 
            project_map = {}
            for pt in project_teams:
                project = pt.project_code
                if not project or project.project_status.lower() != "active":
                    continue
 
                desc = project.project_description.strip().lower()
                if desc in ["internal project", "default project"]:
                    continue
 
                if project_codes and project.project_code not in project_codes:
                    continue
 
                start = max(start_date, pt.start_date, emp.joining_date)
                end = min(end_date, pt.end_date or end_date)
                if start > end:
                    continue
 
                project_map.setdefault(project, []).append((start, end))
 
            for project, ranges in project_map.items():
                ranges.sort()
                merged_ranges = []
                for s, e in ranges:
                    if not merged_ranges or s > merged_ranges[-1][1] + timedelta(days=1):
                        merged_ranges.append([s, e])
                    else:
                        merged_ranges[-1][1] = max(merged_ranges[-1][1], e)
 
                total_missed = 0
                for s, e in merged_ranges:
                    project_days = [d for d in date_list if s <= d <= e]
 
                    allocations = PhaseTeamAllocationHistory.objects.filter(
                        allocation__employee=emp,
                        allocation__project=project
                    ).order_by("allocation_start_date")
 
                    allocation_ranges = []
                    for alloc in allocations:
                        alloc_start = max(start_date, alloc.allocation_start_date, emp.joining_date)
                        alloc_end = min(end_date, alloc.allocation_end_date)
                        if alloc_start <= alloc_end:
                            allocation_ranges.append((alloc_start, alloc_end, alloc.allocation_percent))
 
                    # Merge allocation periods
                    allocation_ranges.sort()
                    merged_allocs = []
                    for s2, e2, p in allocation_ranges:
                        if not merged_allocs or s2 > merged_allocs[-1][1]:
                            merged_allocs.append([s2, e2, p])
                        else:
                            merged_allocs[-1][1] = max(merged_allocs[-1][1], e2)
                            merged_allocs[-1][2] = max(merged_allocs[-1][2], p)
 
                    # EXACT SAME HOURS + EXPECTED HOURS + MISSED LOGIC
                    for alloc_start, alloc_end, alloc_percent in merged_allocs:
                        project_days = [d for d in date_list if alloc_start <= d <= alloc_end]
 
                        expected_hrs = round(8 * (alloc_percent / 100), 2)
 
                        timesheet_data = {d: 0.0 for d in project_days}
 
                        emp_timesheets = EmployeeTimesheet.objects.filter(
                            employee_code=emp.employee_code,
                            project_code=project.project_code,
                            date__range=(alloc_start, alloc_end)
                        )
 
                        for ts in emp_timesheets:
                            if ts.date in timesheet_data:
                                seconds = (ts.worked_hours or timedelta()).total_seconds()
                                timesheet_data[ts.date] += round(seconds / 3600, 2)
 
                        missed_days = [d for d, hrs in timesheet_data.items() if hrs < expected_hrs]
                        total_missed += len(missed_days)
 
                summary.append({
                    "project_name": project.project_description,
                    "project_manager": project.project_manager,
                    "employee_name": emp.name,
                    "missed_dates_count": total_missed,
                })
 
        dedup = []
        seen = set()
        for x in summary:
            key = (x["project_name"], x["project_manager"], x["employee_name"])
            if key not in seen:
                seen.add(key)
                dedup.append(x)
 
        return Response(dedup, status=status.HTTP_200_OK)

    
@swagger_auto_schema(
    method='get',
    operation_summary="Get per-day allocation details for an employee",
    operation_description=(
        "Fetch per-day project allocation details for an employee within a given date range. "
        "Returns all projects the employee is allocated to and allocation percent on each day."
    ),
    manual_parameters=[
        openapi.Parameter(
            'employee_code',
            openapi.IN_QUERY,
            description="Employee code",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'start_date',
            openapi.IN_QUERY,
            description="Start date (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'end_date',
            openapi.IN_QUERY,
            description="End date (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="Employee allocation details successfully retrieved"
        ),
        400: "Bad Request – Missing or invalid parameters",
        404: "Employee not found"
    }
)
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_allocation_timesheet(request):
    employee_code = request.GET.get("employee_code")
    from_date = parse_date(request.GET.get("start_date"))
    to_date = parse_date(request.GET.get("end_date"))

    if not employee_code or not from_date or not to_date:
        return Response({"error": "employee_code, start_date, end_date are required"}, status=400)

    try:
        employee = Employee.objects.get(employee_code=employee_code)
    except Employee.DoesNotExist:
        return Response({"error": "Invalid employee_code"}, status=404)

    # Fetch all PhaseTeamAllocations for the employee
    allocations = PhaseTeamAllocation.objects.filter(employee=employee).select_related("project", "task").prefetch_related("history")

    # Map project_code -> list of allocations
    project_allocs = defaultdict(list)
    for alloc in allocations:
        project_allocs[alloc.project.project_code].append(alloc)

    # Prepare final result structure
    project_map = {}
    total_used = defaultdict(float)

    # Iterate over each date
    curr = from_date
    while curr <= to_date:
        date_str = curr.isoformat()
        for project_code, alloc_list in project_allocs.items():
            daily_details = []
            project_daily = 0.0

            for alloc in alloc_list:
                # Check for history override
                history = alloc.history.filter(
                    allocation_start_date__lte=curr,
                    allocation_end_date__gte=curr
                ).order_by("-updated_at").first()

                if history:
                    percent = history.allocation_percent
                    start_date = history.allocation_start_date
                    end_date = history.allocation_end_date
                else:
                    if alloc.allocation_start_date <= curr <= alloc.allocation_end_date:
                        percent = alloc.allocation_percent
                        start_date = alloc.allocation_start_date
                        end_date = alloc.allocation_end_date
                    else:
                        percent = 0
                        start_date = None
                        end_date = None

                if percent > 0:
                    daily_details.append({
                        "date": date_str,
                        "project_code": project_code,
                        "project_name": alloc.project.project_description,
                        "phase": alloc.task.task_group,
                        "allocation_percent": percent
                    })
                    project_daily += percent

            if daily_details:
                status_flag = "single" if len(daily_details) == 1 else "multiple"
                if project_code not in project_map:
                    project_map[project_code] = {
                        "project_code": project_code,
                        "project_name": alloc_list[0].project.project_description,
                        "log": {}
                    }

                project_map[project_code]["log"][date_str] = {
                    "details": daily_details,
                    "allocation_percent": project_daily,
                    "status_flag": status_flag
                }

                total_used[date_str] += project_daily

        curr += timedelta(days=1)

    # Handle Internal Project (RB001)
    all_dates = [(from_date + timedelta(days=i)).isoformat() for i in range((to_date - from_date).days + 1)]
    internal_log = {}
    for d in all_dates:
        internal_percent = max(0, 100.0 - total_used.get(d, 0))
        internal_log[d] = {
            "details": [
                {
                    "date": d,
                    "project_code": "RB001",
                    "project_name": "Internal Project",
                    "phase": "Internal",
                    "allocation_percent": internal_percent
                }
            ],
            "allocation_percent": internal_percent,
            "status_flag": "single" if internal_percent <= 100.0 else "multiple"
        }

    project_map["RB001"] = {
        "project_code": "RB001",
        "project_name": "Internal Project",
        "log": internal_log
    }

    # Sort each project's log by date
    for proj_code, proj in project_map.items():
        for d in all_dates:
            if d not in proj["log"]:
                proj["log"][d] = {
                    "details": [],
                    "allocation_percent": 0.0,
                    "status_flag": "single"
                }
        proj["log"] = dict(sorted(proj["log"].items()))


    # Return result with RB001 last
    result = [p for code, p in project_map.items() if code != "RB001"]
    result.append(project_map["RB001"])

    return Response(result)

@swagger_auto_schema(
    method='get',
    operation_description="Get all projects filtered by project_type.",
    manual_parameters=[
        openapi.Parameter(
            'project_type',
            openapi.IN_QUERY,
            description="Project Type (Integration, Implementation, Support, Product Development)",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Projects retrieved successfully."
        ),
        404: openapi.Response(description="No projects found for the given project_type."),
        400: openapi.Response(description="Bad request.")
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_projects_by_type(request):
    """
    Get all projects belonging to a specific project_type.
    Output: project_code, country, project_description, project_manager, delivery_head
    """
    project_type = request.GET.get("project_type")

    # Validate input
    valid_types = ["Integration", "Implementation", "Support", "Product Development"]
    if not project_type:
        return Response(
            {"error": "project_type is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if project_type not in valid_types:
        return Response(
            {"error": f"Invalid project_type. Valid values: {valid_types}"},
            status=status.HTTP_400_BAD_REQUEST
        )
    projects = Project.objects.filter(project_type=project_type)

    if not projects.exists():
        return Response(
            {"message": f"No projects found for project_type '{project_type}'."},
            status=status.HTTP_404_NOT_FOUND
        )
    result = [
        {
            "project_code": p.project_code,
            "project_country": p.project_country,
            "project_description": p.project_description,
            "manager": p.project_manager,
            "delivery_head": p.delivery_head,
            "sbu_head":p.sbu_head
        }
        for p in projects
    ]

    return Response(
        {
            "message": f"Projects retrieved successfully for type '{project_type}'.",
            "project_type": project_type,
            "count": len(result),
            "data": result
        },
        status=status.HTTP_200_OK
    )

# def dates_overlap(start1, end1, start2, end2):
#     """Return True if two date ranges overlap."""
#     return start1 <= end2 and start2 <= end1

# # Swagger schema for POST request
# allocation_request_schema = openapi.Schema(
#     type=openapi.TYPE_ARRAY,
#     items=openapi.Items(type=openapi.TYPE_OBJECT, properties={
#         "projectCode": openapi.Schema(type=openapi.TYPE_STRING, description="Project code to update allocation for"),
#         "allocationPercent": openapi.Schema(type=openapi.TYPE_INTEGER, description="Allocation percent (0-100)"),
#         "allocationStartDate": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="Start date of allocation"),
#         "allocationEndDate": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="End date of allocation"),

#     }),
#     description="List of project allocations"
# )

# @swagger_auto_schema(
#     method='get',
#     operation_summary="Get all projects for an employee",
#     operation_description="Returns a list of projects assigned to the given employee along with their allocation details.",
#     responses={
#         200: openapi.Response(
#             description="List of employee projects",
#             examples={
#                 "application/json": [
#                     {
#                         "projectName": "Internal Project",
#                         "projectCode": "RB001",
#                         "managerName": "Kiran Kumar",
#                         "allocationPercent": 0,
#                         "startDate": "2025-09-02",
#                         "endDate": "2125-12-31"
#                     }
#                 ]
#             }
#         ),
#         404: "No projects found for employee"
#     }
# )
# # ================= POST swagger =================
# @swagger_auto_schema(
#     method="post",
#     operation_summary="Add or update project allocation",
#     operation_description="Create or update the allocation percentage for a given employee in a project. Validations ensure total allocation does not exceed 100% for overlapping project dates.",
#     request_body=allocation_request_schema,
#     responses={
#         200: openapi.Response(
#             description="Allocation created or updated successfully",
#             examples={
#                 "application/json": {
#                     "message": "Allocations processed successfully",
#                     "updated": [
#                         {
#                             "projectCode": "QA4",
#                             "allocationPercent": 50,
#                             "message": "updated"
#                         }
#                     ]
#                 }
#             }
#         ),
#         400: "Invalid input / Allocation exceeds 100%",
#         404: "Project not found for employee"
#     }
# )

# @api_view(['GET', 'POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def get_employee_projects(request, employee_code):
#     try:
#         if request.method == 'POST':
#             data = request.data

#             if isinstance(data, dict):
#                 data = [data]
#             if not isinstance(data, list):
#                 return Response({"error": "Request body must be a list or object"}, status=status.HTTP_400_BAD_REQUEST)

#             updated_allocations = []
#             payload_dict = {item['projectCode']: item['allocationPercent'] for item in data if 'projectCode' in item}

#             for item in data:
#                 project_code = item.get('projectCode')
#                 allocation_percent = item.get('allocationPercent')
#                 allocation_start_date = item.get('allocationStartDate')
#                 allocation_end_date = item.get('allocationEndDate')

#                 # === Basic validation ===
#                 if not project_code or allocation_percent is None:
#                     return Response({"error": "Each item must include 'projectCode' and 'allocationPercent'"},
#                                     status=status.HTTP_400_BAD_REQUEST)
#                 if not (0 <= allocation_percent <= 100):
#                     return Response({"error": f"Allocation percent must be between 0 and 100 for project {project_code}"},
#                                     status=status.HTTP_400_BAD_REQUEST)

#                 # === Check if project exists for employee ===
#                 team_qs = ProjectTeam.objects.filter(
#                 employee_code__employee_code=employee_code,
#                 project_code__project_code=project_code
#                 )
#                 if not team_qs.exists():
#                     return Response({"error": f"Project {project_code} not assigned to employee"}, status=status.HTTP_404_NOT_FOUND)

#                 # choose the active phase (based on today's date)
#                 today = date.today()
#                 team = team_qs.filter(start_date__lte=today, end_date__gte=today).first() or team_qs.order_by('-end_date').first()


#                 proj_start = team.start_date
#                 proj_end = team.end_date or proj_start

#                 # === Skip expired projects ===
#                 if proj_end < date.today():
#                     pass

#                 # === Check overlap allocations ===
#                 # === Check overlap allocations ===
#                 existing_allocations = ProjectTeamAllocation.objects.filter(
#                     employee_code=team.employee_code
#                 ).exclude(project_code=team.project_code).select_related('project_code')

#                 # Parse current allocation period from request
#                 curr_alloc_start = (
#                     datetime.strptime(allocation_start_date, "%Y-%m-%d").date()
#                     if allocation_start_date else proj_start
#                 )
#                 curr_alloc_end = (
#                     datetime.strptime(allocation_end_date, "%Y-%m-%d").date()
#                     if allocation_end_date else proj_end
#                 )

#                 # === Validate allocation dates are within project duration ===
#                 if curr_alloc_start < proj_start or curr_alloc_end > proj_end:
#                     return Response({
#                         "error": (
#                             f"Allocation dates for project {project_code} "
#                             f"must be within project duration: {proj_start} to {proj_end}. "
#                             f"Received: {curr_alloc_start} to {curr_alloc_end}"
#                         )
#                     }, status=status.HTTP_400_BAD_REQUEST)

#                 if curr_alloc_end < curr_alloc_start:
#                     return Response({
#                         "error": f"Allocation end date {curr_alloc_end} cannot be before start date {curr_alloc_start} for project {project_code}."
#                     }, status=status.HTTP_400_BAD_REQUEST)


#                 total_allocation_during_overlap = float(allocation_percent)
#                 overlapping_projects = []

#                 for existing in existing_allocations:
#                     existing_team = ProjectTeam.objects.filter(
#                         employee_code=team.employee_code,
#                         project_code=existing.project_code
#                     ).first()
#                     if not existing_team:
#                         continue

#                     existing_proj_start = existing_team.start_date
#                     existing_proj_end = existing_team.end_date or existing_proj_start

#                     # Skip expired allocations
#                     if existing_proj_end < date.today():
#                         continue

#                     # Get existing allocation period
#                     existing_alloc_start = existing.allocation_start_date or existing_proj_start
#                     existing_alloc_end = existing.allocation_end_date or existing_proj_end

#                     if dates_overlap(curr_alloc_start, curr_alloc_end, existing_alloc_start, existing_alloc_end):
#                         payload_allocation = payload_dict.get(existing.project_code.project_code)
#                         allocation_value = float(payload_allocation if payload_allocation is not None else existing.allocation_percent)
#                         total_allocation_during_overlap += allocation_value
#                         overlapping_projects.append((existing.project_code.project_code, allocation_value))

#                 if total_allocation_during_overlap > 100:
#                     return Response({
#                         "error": (
#                             f"Cannot assign allocation for {project_code}. "
#                             f"Total allocation would become {total_allocation_during_overlap}% "
#                             f"due to overlap with: {', '.join([f'{p[0]} ({p[1]}%)' for p in overlapping_projects])}"
#                         )
#                     }, status=status.HTTP_400_BAD_REQUEST)

                
#                 allocation_obj, created = ProjectTeamAllocation.objects.update_or_create(
#                     employee_code=team.employee_code,
#                     project_code=team.project_code,
#                     defaults={
#                         'allocation_percent': allocation_percent,
#                         'allocation_start_date': allocation_start_date,
#                         'allocation_end_date': allocation_end_date
#                     }
#                 )

#             # Always record history, whether created or updated
#                 ProjectTeamAllocationHistory.objects.create(
#                     allocation=allocation_obj,
#                     allocation_percent=allocation_percent,
#                     allocation_start_date=allocation_start_date,
#                     allocation_end_date=allocation_end_date
#                 )

#                 updated_allocations.append({
#                     "projectCode": project_code,
#                     "allocationPercent": allocation_obj.allocation_percent,
#                     "allocationStartDate": allocation_obj.allocation_start_date,
#                     "allocationEndDate": allocation_obj.allocation_end_date,
#                     "message": "created" if created else "updated"
#                 })


#             return Response({
#                 "message": "Allocations processed successfully",
#                 "updated": updated_allocations
#             }, status=status.HTTP_200_OK)


#         project_teams = ProjectTeam.objects.filter(employee_code__employee_code=employee_code)
#         if not project_teams.exists():
#             return Response({"message": f"No projects found for employee {employee_code}"},
#                             status=status.HTTP_404_NOT_FOUND)

#         merged_projects = {}
#         for team in project_teams:
#             project_code = team.project_code.project_code
#             if project_code not in merged_projects:
#                 merged_projects[project_code] = {
#                     "project": team.project_code,
#                     "start_date": team.start_date,
#                     "end_date": team.end_date
#                 }
#             else:
#                 merged_projects[project_code]["start_date"] = min(
#                     merged_projects[project_code]["start_date"], team.start_date
#                 )
#                 merged_projects[project_code]["end_date"] = max(
#                     merged_projects[project_code]["end_date"], team.end_date
#                 )

#         # --- Build response ---
#         response_data = []
#         for project_code, info in merged_projects.items():
#             project = info["project"]
#             proj_start = info["start_date"]
#             proj_end = info["end_date"]

#             allocation = ProjectTeamAllocation.objects.filter(
#                 employee_code__employee_code=employee_code,
#                 project_code__project_code=project_code
#             ).first()

#             allocation_history = []
#             if allocation:
#                 allocation_history = sorted(
#                     [
#                         {
#                             "allocationPercent": h.allocation_percent,
#                             "fromDate": h.allocation_start_date,
#                             "toDate": h.allocation_end_date,
#                             "timestamp": h.updated_at
#                         }
#                         for h in allocation.history.all()
#                         if h.allocation_start_date and h.allocation_end_date
#                         and h.allocation_start_date <= proj_end
#                         and h.allocation_end_date >= proj_start
#                     ],
#                     key=lambda x: x["timestamp"],
#                     reverse=True
#                 )

#             response_data.append({
#                 "projectName": project.project_description,
#                 "projectCode": project.project_code,
#                 "managerName": project.project_manager,
#                 "allocationPercent": allocation.allocation_percent if allocation else 0,
#                 "startDate": proj_start,
#                 "endDate": proj_end,
#                 "allocationStartDate": allocation.allocation_start_date if allocation else None,
#                 "allocationEndDate": allocation.allocation_end_date if allocation else None,
#                 "allocationHistory": allocation_history
#             })



#         return Response(response_data, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

