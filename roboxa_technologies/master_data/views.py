from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
import logging
from drf_yasg import openapi
from .models import ProjectTasks, Employee, ProjectRoles, AssetCategories, AssetModel, Status, Company,Supplier
from .serializers import ProjectTasksSerializer, EmployeeSerializer, ProjectRolesSerializer,EmployeeSummaryRequestSerializer,ProjectUtilizationSerializer, AssetCategoriesSerializer, AssetModelSerializer, StatusSerializer,CompanySerializer,SupplierSerializer
from user_management.serializers import UserCreateSerializer, UserRoleAssignSerializer
from employee.models import EmployeeTimesheet
from datetime import date, datetime,timedelta
import calendar
from django.core.mail import EmailMultiAlternatives
from pmo.models import Project,ProjectTeam,PhaseAllocation,ProjectTeamAllocation
from collections import defaultdict
from user_management.models import UserProfile,UserRoleAssign
from django.db.models import Sum, F
from django.conf import settings
from django.db.models.functions import ExtractMonth
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny


logger = logging.getLogger(__name__)

def generate_random_password(length=12):
    import random
    import string

    length = max(6, min(length, 12))  # Enforce min 6, max 12

    SPECIAL_CHARS = "!@#$%^&*(),.?/:{}|<>"

    # At least one from each category
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice(SPECIAL_CHARS)

    # Remaining characters
    others = random.choices(string.ascii_letters + string.digits + SPECIAL_CHARS, k=length - 4)

    # Shuffle to avoid predictable patterns
    password_list = list(uppercase + lowercase + digit + special + ''.join(others))
    random.shuffle(password_list)

    return ''.join(password_list)
# ---- TASK VIEWS ----
# add task
@swagger_auto_schema(
    method='post',
    operation_description="Add a new task.",
    request_body=ProjectTasksSerializer,
    responses={
        201: openapi.Response("Task created successfully.", ProjectTasksSerializer),
        400: "Bad Request - Validation error."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_task(request):
    serializer = ProjectTasksSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    validated_data = serializer.validated_data
    task_group = validated_data['task_group'].strip().lower()
    description = validated_data['description'].strip().lower()

    # Case-insensitive check for same task_group + description
    if ProjectTasks.objects.filter(
        project_type__iexact=validated_data['project_type'].strip(),
        task_group__iexact=task_group,
        description__iexact=description
    ).exists():
        return Response(
            {"error": "A task with the same description already exists for this phase."},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer.save()
    return Response({
        "message": "Task created successfully.",
        "data": serializer.data
    }, status=status.HTTP_201_CREATED)


# # edit task
# @swagger_auto_schema(
#     method='put',
#     operation_description="Edit an existing task by task code.",
#     request_body=ProjectTasksSerializer,
#     responses={
#         200: openapi.Response("Task updated successfully.", ProjectTasksSerializer),
#         404: "Not Found - Task not found.",
#         400: "Bad Request - Validation error."
#     }
# )
# @api_view(['PUT'])
# def edit_task(request, task_code):
#     try:
#         task = ProjectTasks.objects.get(task_code=task_code)
#     except ProjectTasks.DoesNotExist:
#         return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

#     serializer = ProjectTasksSerializer(task, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({
#             "message": "Task updated successfully.",
#             "data": serializer.data
#         }, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#edit task
@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing task by task code.",
    request_body=ProjectTasksSerializer,
    responses={
        200: openapi.Response("Task updated successfully.", ProjectTasksSerializer),
        404: "Not Found - Task not found.",
        400: "Bad Request - Validation error."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_task(request, task_code):
    try:
        task = ProjectTasks.objects.get(task_code=task_code)
    except ProjectTasks.DoesNotExist:
        return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProjectTasksSerializer(task, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    tg = data.get('task_group', task.task_group).strip()
    desc = data.get('description', task.description).strip()
    pt = data.get('project_type', task.project_type).strip()

    # Duplicate check excluding this task
    duplicates = ProjectTasks.objects.filter(
        project_type__iexact=pt,
        task_group__iexact=tg,
        description__iexact=desc
    ).exclude(task_code=task_code)

    if duplicates.exists():
        return Response(
            {"error": "A task with the same project type, group, and description already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # No duplicates — proceed to update
    serializer.save()
    return Response({
        "message": "Task updated successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)


# display task
@swagger_auto_schema(
    method='get',
    operation_description="Display all tasks.",
    responses={
        200: openapi.Response("Tasks retrieved successfully.", ProjectTasksSerializer(many=True))
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_tasks(request):
    tasks = ProjectTasks.objects.all()
    serializer = ProjectTasksSerializer(tasks, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)

#get descriptions by task
@swagger_auto_schema(
    method='get',
    operation_description="Get descriptions grouped by task group.",
    responses={
        200: openapi.Response("Task descriptions grouped by task group.", openapi.Schema(
            type=openapi.TYPE_OBJECT,
            additional_properties=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
            )
        ))
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def task_descriptions_by_task_group(request):
    tasks = ProjectTasks.objects.values('task_group', 'description')
    
    task_group_map = {}
    for task in tasks:
        task_group = task['task_group']
        description = task['description']
        
        if task_group not in task_group_map:
            # task_group_map[task_group] = []
            task_group_map[task_group] = set() 
        
        # task_group_map[task_group].append(description)
        task_group_map[task_group].add(description)
        # Convert sets back to lists for JSON serialization
    task_group_map = {key: list(values) for key, values in task_group_map.items()}

    return Response(task_group_map, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'project_code',
            openapi.IN_QUERY,
            description="Project code to filter task descriptions by its project type",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    operation_description="Get task descriptions grouped by task group for a given project_code.",
    responses={
        200: openapi.Response("Grouped task descriptions by task group."),
        400: "Project not found"
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def task_descriptions_by_task_group_and_project_code(request):
    project_code = request.GET.get("project_code")

    if not project_code:
        return Response({"error": "project_code is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        project = Project.objects.get(project_code=project_code)
    except Project.DoesNotExist:
        return Response({"error": "Project not found."}, status=status.HTTP_400_BAD_REQUEST)

    project_type = project.project_type

    # Filter tasks for the project_type
    tasks = ProjectTasks.objects.filter(project_type=project_type).values('task_group', 'description')

    task_group_map = {}
    for task in tasks:
        task_group = task['task_group']
        description = task['description']

        if task_group not in task_group_map:
            task_group_map[task_group] = set()

        task_group_map[task_group].add(description)

    # Convert sets to lists for JSON serialization
    task_group_map = {key: list(value) for key, value in task_group_map.items()}

    return Response(task_group_map, status=status.HTTP_200_OK)


# get task byid
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a task by task_id.",
    responses={
        200: openapi.Response("Task retrieved successfully.", ProjectTasksSerializer),
        404: "Not Found - Task not found."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_task_by_id(request, task_code):
    """
    Retrieve a specific task by task_id.
    """
    try:
        task = ProjectTasks.objects.get(task_code=task_code)
    except ProjectTasks.DoesNotExist:
        return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProjectTasksSerializer(task)
    return Response({"task": serializer.data}, status=status.HTTP_200_OK)


# ---- DELETE TASK ----
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a task by task code.",
    responses={
        200: "Task deleted successfully.",
        404: "Not Found - Task not found."
    }
)
@api_view(['DELETE'])
def delete_task(request, task_code):
    try:
        task = ProjectTasks.objects.get(task_code=task_code)
        task.delete()
        return Response({"message": "Task deleted successfully."}, status=status.HTTP_200_OK)
    except ProjectTasks.DoesNotExist:
        return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

# ---- EMPLOYEE VIEWS ----
#add employee
@swagger_auto_schema(
    method='post',
    operation_description="Add a new employee",
    request_body=EmployeeSerializer,
    responses={
        201: openapi.Response("Employee created.", EmployeeSerializer),
        400: "Bad Request - Validation error."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_employee(request):
    serializer = EmployeeSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    employee = serializer.save()
    logger.info(f"Employee {employee.employee_code} created successfully.")

    autogenerated_password = generate_random_password()

    user_data = {
        "user_id": employee.employee_code,
        "name": employee.name,
        "email": employee.email,
        "mobile": employee.mobile,
        "start_date": employee.joining_date,
        "end_date": "2125-12-31",
        "status": "active",
    }

    user_serializer = UserCreateSerializer(data=user_data)
    if not user_serializer.is_valid():
        logger.warning(f"User creation failed: {user_serializer.errors}")
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = user_serializer.save()
    user.set_password(autogenerated_password)
    user.change_password_required = True
    user.save()

    role_data = {
        "user_id": user.user_id,
        "role_name": ["Employee"],
        "name": user.name,
        "email": user.email,
        "mobile": user.mobile,
        "start_date": user.start_date,
        "end_date": user.end_date,
        "status": user.status,
    }

    role_serializer = UserRoleAssignSerializer(data=role_data)
    if role_serializer.is_valid():
        role_serializer.save()
    else:
        logger.warning(f"Role assignment failed: {role_serializer.errors}")

    try:
        if employee.name != "Sudhakara Varma Yarramraju":
            default_project = Project.objects.get(project_code="RB001")
            task_obj = ProjectTasks.objects.filter(
                task_group="Organization Standard Tasks"
            ).first()

            ProjectTeam.objects.create(
                project_code=default_project,
                employee_code=employee,
                employee_name=employee.name,
                designation=employee.designation,
                project_role=ProjectRoles.objects.first(),
                start_date=employee.joining_date,
                end_date="2125-12-31",
                task=task_obj,
                allocated_hours=10000,
            )
            logger.info(f"Employee {employee.employee_code} assigned to RB001 internal project.")
    except Exception as e:
        logger.warning(f"Internal project assignment failed: {e}")

    try:
        subject = "Your PMO Account Credentials"

        plain_message = f"""
Hi {user.name},

Your account has been created.

Here are your login credentials:
Email: {user.email}
Password: {autogenerated_password}

Please log in and change your password immediately.

If you are connected to the 'Roboxa' network, use: http://pmo.roboxaservices.com/
If connected via VPN/external, use: http://pub-pmo.roboxaservices.com/

- ROBOXA TECHNOLOGIES Pvt Ltd.
"""

        html_message = f"""
<html>
<body>
    <p>Hi {user.name},</p>
    <p>Your PMO account has been created successfully. Below are your login credentials:</p>

    <p><strong>Email:</strong> {user.email}<br>
    <strong>Password:</strong> {autogenerated_password}</p>

    <p>Please change your password after logging in.</p>

    <p><strong>For Your Information:</strong><br>
        If you are connected to the <strong>'Roboxa' network</strong>, use:
        <a href="http://pmo.roboxaservices.com/">http://pmo.roboxaservices.com/</a><br>
        Otherwise (VPN / external network), use:
        <a href="http://pub-pmo.roboxaservices.com/">http://pub-pmo.roboxaservices.com/</a></p>

    <p>Best Regards,<br><strong>ROBOXA TECHNOLOGIES Pvt Ltd.</strong></p>
</body>
</html>
"""

        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_msg.attach_alternative(html_message, "text/html")
        email_msg.send()

    except Exception as e:
        logger.warning(f"Email to employee failed: {e}")


    try:
        admin_emails = [
            "pmo-admin@roboxaservices.com",
            "valentina.p@roboxaservices.com"
        ]

        admin_subject = f"New Employee Created: {employee.name}"

        plain_admin_message = f"""
Hello Team,

A new employee has been successfully created in the PMO application.

Employee Details:
Name: {employee.name}
Primary Skills: {getattr(employee, 'skills', 'N/A')}
Secondary Skills: {getattr(employee, 'skills', 'N/A')}
Project Specific Hire: {getattr(employee, 'project_specific_hire', 'N/A')}
Contractor: {getattr(employee, 'contractor', 'N/A')}
Joining Date: {employee.joining_date}

Regards,
PMO System
"""

        html_admin_message = f"""
<html>
<body>
    <p>Hello Team,</p>

    <p>A new employee has been successfully created in the <strong>PMO Application</strong>.</p>

    <p><strong>Employee Details:</strong></p>
    <ul>
        <li><strong>Name:</strong> {employee.name}</li>
        <li><strong>Primary Skills:</strong> {", ".join(getattr(employee, 'primary_skill', [])) if isinstance(getattr(employee, 'primary_skill', []), list) else getattr(employee, 'primary_skill', 'N/A')}</li>
        <li><strong>Secondary Skills:</strong> {", ".join(getattr(employee, 'secondary_skill', [])) if isinstance(getattr(employee, 'secondary_skill', []), list) else getattr(employee, 'secondary_skill', 'N/A')}</li>
        <li><strong>Project Specific Hire:</strong> {getattr(employee, 'project_specific_hire', 'N/A')}</li>
        <li><strong>Contractor:</strong> {getattr(employee, 'contractor', 'N/A')}</li>
        <li><strong>Joining Date:</strong> {employee.joining_date}</li>
    </ul>

    <p>Thanks & Regards,<br><strong>ROBOXA PMO.</strong></p>
</body>
</html>
"""

        admin_email_msg = EmailMultiAlternatives(
            subject=admin_subject,
            body=plain_admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
        )
        admin_email_msg.attach_alternative(html_admin_message, "text/html")
        admin_email_msg.send()

        logger.info("Admin new employee notification email sent.")

    except Exception as e:
        logger.warning(f"Admin notification email failed: {e}")


    try:
        if employee.status.lower() == "inactive" or employee.relieving_date:
            user.is_active = False
            user.status = "inactive"
            user.end_date = employee.relieving_date or user.end_date
            user.save()

            UserRoleAssign.objects.filter(user_id=user.user_id).update(
                status="inactive",
                end_date=user.end_date,
            )

            logger.info(f"User {user.user_id} auto-inactivated due to employee status.")
    except Exception as e:
        logger.warning(f"Auto-deactivation failed: {e}")

    return Response(
        {"message": "Employee created successfully.", "data": serializer.data},
        status=status.HTTP_201_CREATED,
    )


# @swagger_auto_schema(
#     method='post',
#     operation_description="Add a new employee.",
#     request_body=EmployeeSerializer,
#     responses={
#         201: openapi.Response("Employee created.", EmployeeSerializer),
#         400: "Bad Request - Validation error."
#     }
# )
# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def add_employee(request):
#     serializer = EmployeeSerializer(data=request.data)

#     if serializer.is_valid():
#         # Save employee
#         employee = serializer.save()

#         # Log employee creation
#         logger.info(f"Employee {employee.employee_code} created.")

#         return Response({
#             "message": "Employee created successfully.",
#             "data": serializer.data
#         }, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# edit employee
@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing employee by employee code.",
    request_body=EmployeeSerializer,
    responses={
        200: openapi.Response("Employee updated successfully.", EmployeeSerializer),
        404: "Not Found - Employee not found.",
        400: "Bad Request - Validation error."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_employee(request, employee_code):
    try:
        employee = Employee.objects.get(employee_code=employee_code)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    serializer = EmployeeSerializer(employee, data=data, partial=True)

    if serializer.is_valid():
        updated_employee = serializer.save()
        relieving_date = serializer.validated_data.get('relieving_date')

        if relieving_date:
            try:
                user = UserProfile.objects.filter(user_id=employee_code).first()

                if user:
                    user.is_active = False
                    user.status = "inactive"
                    user.end_date = relieving_date
                    user.save()

                    UserRoleAssign.objects.filter(user_id=user.user_id).update(
                        status="inactive",
                        end_date=relieving_date
                    )

                    logger.info(f"User {user.user_id} auto-inactivated (relieving date set).")

            except Exception as e:
                logger.warning(f"Auto-deactivation failed: {e}")

        # --- Detect changes ---
        new_employee_name = serializer.validated_data.get('employee_name') or serializer.validated_data.get('name')
        new_user_name = serializer.validated_data.get('name')
        new_email = serializer.validated_data.get('email')
        new_mobile = serializer.validated_data.get('mobile')

        # --- Fetch linked UserProfile ---
        try:
            user_profile = UserProfile.objects.get(user_id=employee_code)
        except UserProfile.DoesNotExist:
            user_profile = None

        email_changed = new_email and user_profile and user_profile.email != new_email
        auto_generated_password = None

        # If email changed → generate a new password
        if email_changed:
            auto_generated_password = generate_random_password()
            if user_profile:
                user_profile.email = new_email
                user_profile.set_password(auto_generated_password)
                user_profile.change_password_required = True
                user_profile.save()

        # --- Update related tables ---
        if new_user_name:
            if user_profile:
                user_profile.name = new_user_name
                user_profile.save()
            UserRoleAssign.objects.filter(user_id=employee_code).update(name=new_user_name)

        if new_email:
            UserRoleAssign.objects.filter(user_id=employee_code).update(email=new_email)

        if new_mobile:
            if user_profile:
                user_profile.mobile = new_mobile
                user_profile.save()
            UserRoleAssign.objects.filter(user_id=employee_code).update(mobile=new_mobile)

        if new_employee_name:
            ProjectTeam.objects.filter(employee_code=employee_code).update(employee_name=new_employee_name)
            EmployeeTimesheet.objects.filter(employee_code=employee_code).update(employee_name=new_employee_name)

        # --- Send credentials email if email changed ---
        if email_changed and new_email:
            subject = "Your PMO Account Credentials Updated"
            plain_message = f"""
Hi {new_user_name or updated_employee.employee_name},

Your login email has been updated. Here are your new credentials:

Email: {new_email}
Password: {auto_generated_password}

Please login and change your password immediately.

<p><strong>For Your Information:</strong></p>
<p>Please check the network you are connected to and use the appropriate URL below to access the <strong>PMO Application:</strong></p>
<p>If you are connected to the <strong>'Roboxa' network,</strong> please use: http://pmo.roboxaservices.com/</p>
<p>If you are connected otherthan <strong>'Roboxa' network (VPN or external network),</strong> please use: http://pub-pmo.roboxaservices.com/</p>

- ROBOXA TECHNOLOGIES Pvt Ltd.
"""

            html_message = f"""
<html>
<body>
    <p>Hi {new_user_name or updated_employee.employee_name},</p>
    <p>Your login email has been updated. Here are your new credentials:</p>
    <p><strong>Email:</strong> {new_email}<br>
    <strong>Password:</strong> {auto_generated_password}</p>

    <p><strong>For Your Information:</strong></p>
    <p>Please check the network you are connected to and use the appropriate URL below to access the <strong>PMO Application:</strong></p>
    <p>If you are connected to the <strong>'Roboxa' network,</strong> please use: http://pmo.roboxaservices.com/</p>
    <p>If you are connected otherthan <strong>'Roboxa' network (VPN or external network),</strong> please use: http://pub-pmo.roboxaservices.com/</p>

    <p><strong>Please change your password after logging in.</strong></p>
    <p>Best Regards,<br><strong>ROBOXA TECHNOLOGIES Pvt Ltd.</strong></p>
</body>
</html>
"""
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[new_email],
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send()

            
            # AUTO-DEACTIVATE user & roles if employee is inactive
            employee = Employee.objects.get(employee_code=employee_code)
            user = UserProfile.objects.filter(user_id=employee.employee_code).first()

            if user:
                if employee.status.lower() == "inactive" or employee.relieving_date:
                    user.is_active = False
                    user.status = "inactive"
                    user.end_date = employee.relieving_date or user.end_date
                    user.save()

                    UserRoleAssign.objects.filter(user_id=user.user_id).update(
                        status="inactive",
                        end_date=employee.relieving_date or user.end_date
                    )

                    logger.info(f"User {user.user_id} auto-inactivated due to employee update.")


        return Response({
            "message": "Employee updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# edit employee
# @swagger_auto_schema(
#     method='put',
#     operation_description="Edit an existing employee by employee code.",
#     request_body=EmployeeSerializer,
#     responses={
#         200: openapi.Response("Employee updated successfully.", EmployeeSerializer),
#         404: "Not Found - Employee not found.",
#         400: "Bad Request - Validation error."
#     }
# )
# @api_view(['PUT'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def edit_employee(request, employee_code):
#     try:
#         employee = Employee.objects.get(employee_code=employee_code)
#     except Employee.DoesNotExist:
#         return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

#     data = request.data.copy()
#     serializer = EmployeeSerializer(employee, data=data, partial=True)

#     if serializer.is_valid():
#         updated_employee = serializer.save()

#         # --- Detect changes ---
#         new_employee_name = serializer.validated_data.get('employee_name') or serializer.validated_data.get('name')
#         new_user_name = serializer.validated_data.get('name')
#         new_email = serializer.validated_data.get('email')
#         new_mobile = serializer.validated_data.get('mobile')

#         # --- Fetch linked UserProfile ---
#         try:
#             user_profile = UserProfile.objects.get(user_id=employee_code)
#         except UserProfile.DoesNotExist:
#             user_profile = None

#         email_changed = new_email and user_profile and user_profile.email != new_email
#         auto_generated_password = None

#         # If email changed → generate a new password
#         if email_changed:
#             auto_generated_password = generate_random_password()
#             if user_profile:
#                 user_profile.email = new_email
#                 user_profile.set_password(auto_generated_password)
#                 user_profile.change_password_required = True
#                 user_profile.save()

#         # --- Update related tables ---
#         if new_user_name:
#             if user_profile:
#                 user_profile.name = new_user_name
#                 user_profile.save()
#             UserRoleAssign.objects.filter(user_id=employee_code).update(name=new_user_name)

#         if new_email:
#             UserRoleAssign.objects.filter(user_id=employee_code).update(email=new_email)

#         if new_mobile:
#             if user_profile:
#                 user_profile.mobile = new_mobile
#                 user_profile.save()
#             UserRoleAssign.objects.filter(user_id=employee_code).update(mobile=new_mobile)

#         if new_employee_name:
#             ProjectTeam.objects.filter(employee_code=employee_code).update(employee_name=new_employee_name)
#             EmployeeTimesheet.objects.filter(employee_code=employee_code).update(employee_name=new_employee_name)

#         # --- Send credentials email if email changed ---
#         if email_changed and new_email:
#             subject = "Your PMO Account Credentials Updated"
#             plain_message = f"""
# Hi {new_user_name or updated_employee.employee_name},

# Your login email has been updated. Here are your new credentials:

# Email: {new_email}
# Password: {auto_generated_password}

# Please login and change your password immediately.

# <p><strong>For Your Information:</strong></p>
# <p>Please check the network you are connected to and use the appropriate URL below to access the <strong>PMO Application:</strong></p>
# <p>If you are connected to the <strong>'Roboxa' network,</strong> please use: http://pmo.roboxaservices.com/</p>
# <p>If you are connected otherthan <strong>'Roboxa' network (VPN or external network),</strong> please use: http://pub-pmo.roboxaservices.com/</p>

# - ROBOXA TECHNOLOGIES Pvt Ltd.
# """

#             html_message = f"""
# <html>
# <body>
#     <p>Hi {new_user_name or updated_employee.employee_name},</p>
#     <p>Your login email has been updated. Here are your new credentials:</p>
#     <p><strong>Email:</strong> {new_email}<br>
#     <strong>Password:</strong> {auto_generated_password}</p>

#     <p><strong>For Your Information:</strong></p>
#     <p>Please check the network you are connected to and use the appropriate URL below to access the <strong>PMO Application:</strong></p>
#     <p>If you are connected to the <strong>'Roboxa' network,</strong> please use: http://pmo.roboxaservices.com/</p>
#     <p>If you are connected otherthan <strong>'Roboxa' network (VPN or external network),</strong> please use: http://pub-pmo.roboxaservices.com/</p>

#     <p><strong>Please change your password after logging in.</strong></p>
#     <p>Best Regards,<br><strong>ROBOXA TECHNOLOGIES Pvt Ltd.</strong></p>
# </body>
# </html>
# """
#             email_msg = EmailMultiAlternatives(
#                 subject=subject,
#                 body=plain_message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[new_email],
#             )
#             email_msg.attach_alternative(html_message, "text/html")
#             email_msg.send()

#         return Response({
#             "message": "Employee updated successfully.",
#             "data": serializer.data
#         }, status=status.HTTP_200_OK)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#display employee
# @swagger_auto_schema(
#     method='get',
#     operation_description="Display all employees.",
#     responses={
#         200: openapi.Response("Employees retrieved successfully.", EmployeeSerializer(many=True))
#     }
# )
# @api_view(['GET'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def display_employee(request):
#     employees = Employee.objects.all()
#     serializer = EmployeeSerializer(employees, many=True)
#     return Response({"data": serializer.data}, status=status.HTTP_200_OK)

#display employee
@swagger_auto_schema(
    method='get',
    operation_description="Display all employees.",
    responses={
        200: openapi.Response("Employees retrieved successfully.", EmployeeSerializer(many=True))
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_employee(request):
    employees = Employee.objects.all()
    response_data = []

    for emp in employees:
        # Serialize base employee data
        serialized_emp = EmployeeSerializer(emp).data

        # Fetch corresponding user
        user = UserProfile.objects.filter(user_id=emp.employee_code).first()

        # Default roles to empty
        roles = []

        if user:
            role_assignments = UserRoleAssign.objects.filter(user_id=user.user_id)
            # Flatten all role_name lists
            roles = list(set(role for assignment in role_assignments for role in assignment.role_name))

        # Add roles to serialized employee
        serialized_emp['roles'] = roles
        response_data.append(serialized_emp)

    return Response({"data": response_data}, status=status.HTTP_200_OK)



# get employee by id
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve an employee by employee_id.",
    responses={
        200: openapi.Response("Employee retrieved successfully.", EmployeeSerializer),
        404: "Not Found - Employee not found."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_employee_by_id(request, employee_code):
    """
    Retrieve a specific employee by employee_id.
    """
    try:
        employee = Employee.objects.get(employee_code=employee_code)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmployeeSerializer(employee)
    return Response({"employee": serializer.data}, status=status.HTTP_200_OK)


# ---- DELETE EMPLOYEE ----
@swagger_auto_schema(
    method='delete',
    operation_description="Delete an employee by employee code.",
    responses={
        200: "Employee record deleted successfully.",
        404: "Not Found - Employee not found.",
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_employee(request, employee_code):
    try:
        employee = Employee.objects.get(employee_code=employee_code)
        employee.delete()
        return Response({"message": "Employee record deleted successfully."}, status=status.HTTP_200_OK)
    except Employee.DoesNotExist:
        return Response({"error": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)


# ---- PROJECT ROLES VIEWS ----
# add projectroles
@swagger_auto_schema(
    method='post',
    operation_description="Add a new project role.",
    request_body=ProjectRolesSerializer,
    responses={
        201: openapi.Response("Project role created successfully.", ProjectRolesSerializer),
        400: "Bad Request - Validation error."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def add_project_role(request):
    serializer = ProjectRolesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Project role created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    # Custom error handling
    error_message = serializer.errors.get("project_role", [])
    if "project roles with this project role already exists." in error_message:
        return Response({"error": "Duplicate project role not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# display projectroles
@swagger_auto_schema(
    method='get',
    operation_description="Display all project roles.",
    responses={
        200: openapi.Response("Project roles retrieved successfully.", ProjectRolesSerializer(many=True))
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def display_project_roles(request):
    roles = ProjectRoles.objects.all()
    serializer = ProjectRolesSerializer(roles, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)

# get projectrole byid
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a project role by role_id.",
    responses={
        200: openapi.Response("Project role retrieved successfully.", ProjectRolesSerializer),
        404: "Not Found - Project role not found."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_project_role_by_id(request, role_id):
    """
    Retrieve a specific project role by role_id.
    """
    try:
        role = ProjectRoles.objects.get(id=role_id)
    except ProjectRoles.DoesNotExist:
        return Response({"error": "Project role not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProjectRolesSerializer(role)
    return Response({"project_role": serializer.data}, status=status.HTTP_200_OK)

# edit project role by id
@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing project role by ID.",
    request_body=ProjectRolesSerializer,
    responses={
        200: openapi.Response("Project role updated successfully.", ProjectRolesSerializer),
        404: "Not Found - Project role not found.",
        400: "Bad Request - Validation error."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_project_role(request, role_id):
    try:
        role = ProjectRoles.objects.get(id=role_id)
    except ProjectRoles.DoesNotExist:
        return Response({"error": "Project role not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProjectRolesSerializer(role, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "message": "Project role updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ---- DELETE PROJECT ROLE ----
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a project role by ID.",
    responses={
        200: "Project role deleted successfully.",
        404: "Not Found - Project role not found."
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_project_role(request, role_id):
    try:
        role = ProjectRoles.objects.get(id=role_id)
        role.delete()
        return Response({"message": "Project role deleted successfully."}, status=status.HTTP_200_OK)
    except ProjectRoles.DoesNotExist:
        return Response({"error": "Project role not found."}, status=status.HTTP_404_NOT_FOUND)

# get employee summary report  
@swagger_auto_schema(
    method='post',
    operation_description="Get Employee Summary Report.",
    request_body=EmployeeSummaryRequestSerializer,
    responses={200: "Success", 400: "Validation error"}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_summary_report(request):
    serializer = EmployeeSummaryRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    month = data['month']
    year = data['year']
    employee_code = data.get('employee_code', [])  # list of employee codes
    country = data.get('country', '').strip()

    employee_filter = {}

    if employee_code:  # list of strings
        employee_filter['employee_code__in'] = employee_code

    if country:
        employee_filter['country'] = country
    employees = Employee.objects.filter(**employee_filter)

    summary_report = []

    for employee in employees:
        # Filter only approved timesheets for the employee for the given month and year
        timesheets = EmployeeTimesheet.objects.filter(
            employee_code=employee.employee_code,
            month=month,
            year=year,
            # status__iexact='approved'  # Only consider approved timesheets
        ).exclude(status__iexact='rejected')

        total_worked_hours = timedelta()
        total_leave_hours = timedelta()
        total_holiday_hours = timedelta()

        # Process each approved timesheet entry
        for entry in timesheets:
            # worked = entry.worked_hours if entry.status and entry.status.lower() == 'approved' else timedelta()
            worked = entry.worked_hours or timedelta()

            # Add leave hours separately
            desc = (entry.new_description or '').strip().lower()
            if desc == 'full day leave':
                total_leave_hours += timedelta(hours=8)
            elif desc == 'half day leave':
                total_leave_hours += timedelta(hours=4)
            elif desc == 'sick leave':
                total_leave_hours += worked  # Actual worked hours used as leave
            elif desc == 'holiday' or desc == 'client holiday':
                total_holiday_hours += timedelta(hours=8)
            else:
                total_worked_hours += worked  # only non-leave entries go here

            # total_worked_hours += worked

        total_booked_hours = total_worked_hours + total_leave_hours + total_holiday_hours

        def calculate_total_hours(month, year):
            total_days = calendar.monthrange(year, month)[1]
            working_days = sum(
                1 for day in range(1, total_days + 1)
                if date(year, month, day).weekday() < 5
            )
            return timedelta(hours=working_days * 8)

        # approved_hours = timedelta()
        # for entry in timesheets:
        #     desc = (entry.new_description or '').strip().lower()
        #     if entry.status and entry.status.lower() == 'approved':
        #         if desc not in ['full day leave', 'half day leave', 'holiday', 'client holiday', 'sick leave']:
        #             approved_hours += entry.worked_hours or timedelta()
        approved_hours = timedelta()
        for entry in timesheets:
            desc = (entry.new_description or '').strip().lower()
            if entry.status and entry.status.lower() == 'approved':
                if desc in ['full day leave', 'holiday', 'client holiday']:
                    approved_hours += timedelta(hours=8)
                elif desc == 'half day leave':
                    approved_hours += timedelta(hours=4)
                elif desc == 'sick leave':
                    approved_hours += entry.worked_hours or timedelta()
                else:
                    approved_hours += entry.worked_hours or timedelta()

        total_expected_hours = calculate_total_hours(month, year)

        def format_td(td):
            total_seconds = int(td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02}:{minutes:02}"

        balance_hours = total_expected_hours - total_booked_hours
        approved_diff = total_booked_hours - approved_hours

        # Append employee summary report
        summary_report.append({
            "month": month,
            "year": year,
            "employee_id": employee.employee_code,
            "employee_name": employee.name,
            "country": employee.country if employee.country else "",
            "designation": employee.designation,
            "total_hours": int(total_expected_hours.total_seconds() // 3600),
            "total_worked_hours": format_td(total_worked_hours),
            "leave_hours": int(total_leave_hours.total_seconds() // 3600),
            "holiday_hours": int(total_holiday_hours.total_seconds() // 3600),
            "total_booked_hours":format_td(total_booked_hours),
            "approved_hours": format_td(approved_hours),
            "balance_hours": format_td(balance_hours),
            "approved_diff": format_td(approved_diff)
        })

    return Response({"summary_report": summary_report}, status=status.HTTP_200_OK)


#get employee summary report detailed  
@swagger_auto_schema(
    method='post',
    operation_description="Get Employee Summary Report Detailed.",
    request_body=EmployeeSummaryRequestSerializer,
    responses={200: "Success", 400: "Validation error"}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_summary_report_detailed(request):
    serializer = EmployeeSummaryRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    month = data['month']
    year = data['year']
    employee_code = data.get('employee_code', [])  # list of employee codes
    country = data.get('country', '').strip()

    employee_filter = {}

    if employee_code:  # list of strings
        employee_filter['employee_code__in'] = employee_code

    if country:
        employee_filter['country'] = country
    employees = Employee.objects.filter(**employee_filter)

    detailed_report = []

    for employee in employees:
        timesheets = EmployeeTimesheet.objects.filter(
            employee_code=employee.employee_code,
            month=month,
            year=year
        ).exclude(status__iexact='rejected')

        for entry in timesheets:
            # Add worked and leave hours based on description
            worked_hours = entry.worked_hours if (entry.new_description or '').strip().lower() not in ['full day leave', 'holiday', 'half day leave'] else timedelta()
            leave_hours = timedelta()
            holiday_hours = timedelta()

            desc = (entry.new_description or '').strip().lower()
            if desc in ['client holiday', 'holiday']:
                holiday_hours = timedelta(hours=8)
            elif desc in ['full day leave', 'sick leave']:
                leave_hours = timedelta(hours=8)
            elif desc == 'half day leave':
                leave_hours = timedelta(hours=4)
            else:
                worked_hours = entry.worked_hours


            worked_hours = entry.worked_hours if desc not in ['full day leave', 'half day leave', 'holiday', 'client holiday', 'sick leave'] else timedelta()

            total_booked = worked_hours + leave_hours + holiday_hours 


            # Calculate the total approved hours (if any)
            approved_hours = timedelta()
            if entry.status and entry.status.lower() == 'approved':
                approved_hours += worked_hours

            # Use the formatting function for time
            # def format_td(td):
            #     total_seconds = int(td.total_seconds())
            #     hours = total_seconds // 3600
            #     minutes = (total_seconds % 3600) // 60
            #     seconds = total_seconds % 60
            #     return f"{hours:02}:{minutes:02}:{seconds:02}"
            def format_td(td):
                total_seconds = int(td.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{hours:02}:{minutes:02}"
        
            project_manager = ""
            project_name = ""

            if entry.project_code:
                project_manager = entry.project_code.project_manager
                project_name = entry.project_code.project_description


            # approved_hours = worked_hours if entry.status and entry.status.lower() == 'approved' else timedelta()
            approved_hours = timedelta()
            if entry.status and entry.status.lower() == 'approved':
                # Add worked hours if it's a normal working day
                if desc not in ['full day leave', 'half day leave', 'holiday', 'client holiday', 'sick leave']:
                    approved_hours += worked_hours
                # Add leave and holiday hours if approved
                approved_hours += leave_hours + holiday_hours

            approved_diff = total_booked - approved_hours
            # Add the detailed report entry
            detailed_report.append({
                "date": entry.date.strftime("%Y-%m-%d"),
                "month": month,
                "year": year,
                "employee_id": employee.employee_code,
                "employee_name": employee.name,
                "project_manager": project_manager,
                "project_name": project_name,
                "country": employee.country if employee.country else "",
                "designation": employee.designation,
                "worked_hours": format_td(worked_hours),
                "leave_hours": int(leave_hours.total_seconds() // 3600),
                "holiday_hours":int(holiday_hours.total_seconds() // 3600),
                "total_booked_hours": format_td(total_booked),
                "approved_hours": format_td(approved_hours),
                # "description": entry.new_description,
                "approved_diff": format_td(approved_diff)
            })

    return Response({"detailed_report": detailed_report}, status=status.HTTP_200_OK)

#employee summary report by project
@swagger_auto_schema(
    method='post',
    operation_description="Get Employee Summary Detailed Report grouped by Project.",
    request_body=EmployeeSummaryRequestSerializer,
    responses={200: "Success", 400: "Validation error"}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def employee_summary_report_detailed_by_project(request):
    serializer = EmployeeSummaryRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    month = data['month']
    year = data['year']
    employee_code = data.get('employee_code', [])  # from validated_data
    country = data.get('country', '').strip()

    employee_filter = {}
    if employee_code:  # list of employee codes
        employee_filter['employee_code__in'] = employee_code
    if country:
        employee_filter['country'] = country


    employees = Employee.objects.filter(**employee_filter)

    summary_data = defaultdict(lambda: {
        "total_hours": timedelta(),
        "open_hours": timedelta(),
        "approved_hours": timedelta(),
        "leave_hours": 0,
        "holiday_hours": 0,
        "employee": None,
        "project_name": "",
        "project_manager": ""
    })

    def format_td(td):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02}:{minutes:02}"

    for employee in employees:
        # 1. Fetch assigned projects
        assigned_projects = ProjectTeam.objects.filter(
            employee_code=employee.employee_code,
            start_date__lte=date(year, month, calendar.monthrange(year, month)[1]),
            end_date__gte=date(year, month, 1)
        )

        for proj in assigned_projects:
            proj_code = proj.project_code.project_code if proj.project_code else "NA"
            key = (employee.employee_code, proj_code)
            entry_data = summary_data[key]
            if not entry_data["employee"]:
                entry_data["employee"] = employee
                entry_data["project_name"] = proj.project_code.project_description
                entry_data["project_manager"] = proj.project_code.project_manager

        # 2. Fetch timesheets
        timesheets = EmployeeTimesheet.objects.filter(
            employee_code=employee.employee_code,
            month=month,
            year=year
        )

        for entry in timesheets:
            desc = (entry.new_description or '').strip().lower()
            entry_status = (entry.status or '').strip().lower()

            leave = 0
            holiday = 0
            worked = timedelta()
            approved = timedelta()
            open_hours = timedelta()

            if desc in ['full day leave', 'sick leave']:
                leave = 8
            elif desc == 'half day leave':
                leave = 4
            elif desc in ['holiday', 'client holiday']:
                holiday = 8
            elif entry_status in ['approved', 'open']:
                worked = entry.worked_hours
                if entry_status == 'approved':
                    approved = entry.worked_hours
                elif entry_status == 'open':
                    open_hours = entry.worked_hours

            proj_code = entry.project_code.project_code if entry.project_code else "NA"
            key = (employee.employee_code, proj_code)
            entry_data = summary_data[key]

            # Fill employee/project data if not already
            if not entry_data["employee"]:
                entry_data["employee"] = employee
                if entry.project_code:
                    entry_data["project_name"] = entry.project_code.project_description
                    entry_data["project_manager"] = entry.project_code.project_manager

            if desc in ['full day leave', 'half day leave', 'sick leave']:
                if entry_status == 'approved':
                    entry_data["leave_hours"] += leave
                    entry_data["approved_hours"] += timedelta(hours=leave)
                elif entry_status == 'open':
                    entry_data["leave_hours"] += leave
            elif desc in ['holiday', 'client holiday']:
                entry_data["holiday_hours"] += holiday
                if entry_status == 'approved':
                    entry_data["approved_hours"] += timedelta(hours=holiday)
            else:
                if entry_status == 'approved':
                    entry_data["approved_hours"] += approved
                    entry_data["total_hours"] += worked
                elif entry_status == 'open':
                    entry_data["open_hours"] += open_hours
                    entry_data["total_hours"] += worked

    # 3. Format final report
    detailed_report = []

    for (emp_code, project_code), summary in summary_data.items():
        emp = summary["employee"]
        worked = summary["total_hours"]
        approved = summary["approved_hours"]
        open_hours = summary["open_hours"]
        leave_hours = summary["leave_hours"]
        holiday_hours = summary["holiday_hours"]
        total_booked = worked + timedelta(hours=leave_hours + holiday_hours)

        detailed_report.append({
            "month": month,
            "year": year,
            "employee_id": emp.employee_code,
            "employee_name": emp.name,
            "project_manager": summary["project_manager"],
            "project_code": project_code,
            "project_name": summary["project_name"],
            "country": emp.country or "",
            "designation": emp.designation,
            "worked_hours": format_td(worked),
            "leave_hours": leave_hours,
            "holiday_hours": holiday_hours,
            "total_booked_hours": format_td(total_booked),
            "approved_hours": format_td(approved),
            "approved_diff": format_td(total_booked - approved)
        })

    return Response({"detailed_report_project": detailed_report}, status=status.HTTP_200_OK)

class EmployeeDashboard(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request, year, employee_code):
        # Define the financial year
        start_date = datetime(year, 4, 1).date()
        end_date = datetime(year + 1, 3, 31).date()

        employee = Employee.objects.get(employee_code=employee_code)
        joining_date = employee.joining_date

        # Apply effective start date based on employee's joining date
        effective_start_date = max(start_date, joining_date)
        # effective_start_date = start_date

        # Calculate overall working days and target utilization
        working_days = self.calculate_working_days(effective_start_date, end_date)
        target_utilization = working_days * 8  # 8 hours per working day

        worked_hours_by_month = {}
        month_targets = {}
        total_worked_hours = 0

        # Approved worked hours in the financial year
        approved_worked_hours = EmployeeTimesheet.objects.filter(
            date__range=(effective_start_date, end_date),
            employee_code__employee_code=employee_code,
            status='approved'
        ).annotate(
            month_val=ExtractMonth('date')
        ).values('month_val').annotate(
            total=Sum('worked_hours')
        ).order_by('month_val')

        # Process worked hours
        for entry in approved_worked_hours:
            month = entry.get('month_val')
            total = entry.get('total')

            # Handle different types of 'total'
            if isinstance(total, timedelta):
                hours = total.total_seconds() / 3600
            elif isinstance(total, (int, float)):
                hours = float(total)
            elif isinstance(total, str):
                try:
                    hours = float(total)
                except ValueError:
                    hours = 0.0
            else:
                hours = 0.0  # fallback

            month_start = datetime(year if month >= 4 else year + 1, month, 1).date()
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            month_working_days = self.calculate_working_days(max(effective_start_date, month_start), min(end_date, month_end))
            month_target_hours = month_working_days * 8
            month_targets[month] = month_target_hours 

            utilization = (hours / month_target_hours * 100) if month_target_hours else 0
            # formatted = f"{int(hours)} ({round(utilization)}%)"
            formatted = f"{int(hours)} ({utilization:.2f}%)"

            worked_hours_by_month[month] = formatted
            total_worked_hours += hours


        # Fill missing months with 0 (0%)
        for m in range(1, 13):
            if m not in worked_hours_by_month:
                worked_hours_by_month[m] = "0 (0%)"
                # Also fill targets to avoid key errors
                month_year = year if m >= 4 else year + 1
                month_start = datetime(month_year, m, 1).date()
                month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                effective_month_start = max(month_start, effective_start_date)
                effective_month_end = min(month_end, end_date)
                month_targets[m] = self.calculate_working_days(effective_month_start, effective_month_end) * 8

        utilization_percentage = (total_worked_hours / target_utilization * 100) if target_utilization else 0
        meter_percentage = round(utilization_percentage, 2)

        chart_labels = [
            "Q1", f"Apr {year}", f"May {year}", f"Jun {year}",
            "Q2", f"Jul {year}", f"Aug {year}", f"Sep {year}",
            "Q3", f"Oct {year}", f"Nov {year}", f"Dec {year}",
            "Q4", f"Jan {year+1}", f"Feb {year+1}", f"Mar {year+1}",
        ]

        def extract_hours(val):
            return float(val.split()[0]) if isinstance(val, str) and '(' in val else 0

        def quarter_data(months):
            actual_hours = sum([extract_hours(worked_hours_by_month.get(m)) for m in months])
            possible_hours = sum([month_targets.get(m, 0) for m in months])
            percent = (actual_hours / possible_hours * 100) if possible_hours else 0
            # return f"{int(actual_hours)} ({int(percent)}%)"
            return f"{int(actual_hours)} ({percent:.2f}%)"


        chart_data = [
            quarter_data([4, 5, 6]), worked_hours_by_month[4], worked_hours_by_month[5], worked_hours_by_month[6],
            quarter_data([7, 8, 9]), worked_hours_by_month[7], worked_hours_by_month[8], worked_hours_by_month[9],
            quarter_data([10, 11, 12]), worked_hours_by_month[10], worked_hours_by_month[11], worked_hours_by_month[12],
            quarter_data([1, 2, 3]), worked_hours_by_month[1], worked_hours_by_month[2], worked_hours_by_month[3],
        ]

        # === PENDING DATA calculation (date-wise missing hours combined across projects) ===
        # Set fixed default project start date
        # === UPDATED PENDING DATA calculation ===
        default_start_date = date(2025, 4, 1)
        today = date.today()

        # All project teams for this employee
        project_teams = ProjectTeam.objects.filter(employee_code__employee_code=employee_code).select_related('project_code', 'task')

        pending_data = []

        # Effective global start (employee joining or financial/default start)
        effective_global_start = max(employee.joining_date, default_start_date)
        effective_global_end = today  # include today

        # Build project -> list(phases)
        project_map = defaultdict(list)
        for pt in project_teams:
            project_map[pt.project_code].append(pt)

        # Helper to parse hours (reuse your logic)
        def parse_hours_value(val):
            if val is None:
                return 0.0
            if isinstance(val, timedelta):
                return val.total_seconds() / 3600
            if isinstance(val, (int, float)):
                return float(val)
            s = str(val).strip()
            if s.replace('.', '', 1).isdigit():
                return round(float(s), 2)
            parts = s.split(':')
            try:
                if len(parts) == 2:
                    h, m = int(parts[0]), int(parts[1])
                    return round(h + m/60, 2)
                if len(parts) == 3:
                    h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
                    return round(h + m/60 + sec/3600, 2)
            except:
                return 0.0
            return 0.0

        # Determine expected hours per project (allocation% * 8)
        expected_per_project = {}
        for project_obj, phases in project_map.items():
            alloc_obj = ProjectTeamAllocation.objects.filter(employee_code=employee, project_code=project_obj).first()
            allocation_percent = alloc_obj.allocation_percent if alloc_obj else 0.0
            expected_per_project[project_obj.project_code] = round((allocation_percent / 100.0) * 8.0, 2)

        # If there's an internal project, let it take the remainder so daily expected can reach 8
        total_expected = sum(expected_per_project.values())
        internal_project_code = None
        if total_expected < 8.0:
            # find a project whose description is Internal Project (case-insensitive)
            for p in expected_per_project.keys():
                # fetch project object from map keys
                # keys in expected_per_project are project.project_code strings, but earlier we used project_obj.project_code
                pass

        # Map project_code string -> project object (for lookups)
        projcode_to_obj = {p.project_code: p for p in project_map.keys()}

        # find actual project object name for internal project if present
        internal_obj = None
        for proj_obj in project_map.keys():
            try:
                if proj_obj.project_description and proj_obj.project_description.strip().lower() == "internal project":
                    internal_obj = proj_obj
                    internal_project_code = proj_obj.project_code
                    break
            except:
                continue

        if internal_obj and total_expected < 8.0:
            diff = round(8.0 - total_expected, 2)
            # add diff to internal project's expected hours
            expected_per_project[internal_project_code] = expected_per_project.get(internal_project_code, 0.0) + diff
            total_expected = sum(expected_per_project.values())

        # Build a dict of all timesheets for the employee in the big date window (approved/open)
        timesheet_qs = EmployeeTimesheet.objects.filter(
            employee_code__employee_code=employee_code,
            date__range=(effective_global_start, effective_global_end),
            status__in=['approved', 'open']
        ).select_related('project_code')

        # worked_hours_by_project_date[proj_code_str][date] = hours
        worked_hours_by_project_date = defaultdict(lambda: defaultdict(float))
        for ts in timesheet_qs:
            proj_code_str = ts.project_code.project_code if ts.project_code else None
            if proj_code_str:
                hrs = parse_hours_value(ts.worked_hours)
                worked_hours_by_project_date[proj_code_str][ts.date] += hrs

        # Now iterate per project and compute missing per its phase window
        for project_obj, phases in project_map.items():
            project_code_str = project_obj.project_code

            min_phase_start = min([p.start_date for p in phases])
            max_phase_end = max([(p.end_date or today) for p in phases])

            # Count window limited by global effective range
            count_start = max(effective_global_start, min_phase_start)
            count_end = min(effective_global_end, max_phase_end)

            # build list of working days in this project's count window
            project_dates = []
            cur = count_start
            while cur <= count_end:
                if cur.weekday() < 5:
                    project_dates.append(cur)
                cur += timedelta(days=1)

            if not project_dates:
                # still append metadata with zero missing
                allocation_obj = ProjectTeamAllocation.objects.filter(employee_code=employee, project_code=project_obj).first()
                allocation_percent = allocation_obj.allocation_percent if allocation_obj else 0.0
                pending_data.append({
                    "project_code": project_obj.project_code,
                    "project_description": project_obj.project_description,
                    "employee_name": employee.name,
                    "count_start_date": count_start,
                    "count_end_date": count_end,
                    "project_start_date": project_obj.from_date if hasattr(project_obj, 'from_date') else None,
                    "project_end_date": project_obj.to_date if hasattr(project_obj, 'to_date') else None,
                    "phase": ", ".join(sorted({p.task.task_group for p in phases if p.task})),
                    "project_manager": project_obj.project_manager,
                    "no_of_days_missing_entry": 0,
                    "allocation_percent": allocation_percent
                })
                continue

            # expected hours for this project (use project_code string as key)
            expected = expected_per_project.get(project_code_str, round(8.0 * 1.0, 2) if not project_teams else 0.0)

            missing_dates = []
            for d in project_dates:
                proj_hours = worked_hours_by_project_date.get(project_code_str, {}).get(d, 0.0)

                # Internal project special override: if internal project has >= 8 hrs on this date, consider project filled
                if internal_project_code and internal_project_code != project_code_str:
                    internal_hours_on_date = worked_hours_by_project_date.get(internal_project_code, {}).get(d, 0.0)
                    if internal_hours_on_date >= 8.0:
                        # treat as filled for all projects on this date
                        continue

                # If project hours < expected -> missing
                if round(proj_hours, 2) < round(expected, 2):
                    missing_dates.append(d)

            allocation_obj = ProjectTeamAllocation.objects.filter(employee_code=employee, project_code=project_obj).first()
            allocation_percent = allocation_obj.allocation_percent if allocation_obj else 0.0

            pending_data.append({
                "project_code": project_obj.project_code,
                "project_description": project_obj.project_description,
                "employee_name": employee.name,
                "count_start_date": count_start,
                "count_end_date": count_end,
                "project_start_date": project_obj.from_date if hasattr(project_obj, 'from_date') else None,
                "project_end_date": project_obj.to_date if hasattr(project_obj, 'to_date') else None,
                "phase": ", ".join(sorted({p.task.task_group for p in phases if p.task})),
                "project_manager": project_obj.project_manager,
                "no_of_days_missing_entry": len(missing_dates),
                "allocation_percent": allocation_percent
            })

        # === UTILIZATION TILL DATE ===
        today = date.today()
        till_date_working_days = self.calculate_working_days(effective_start_date, today)
        target_utilization_till_date = till_date_working_days * 8

        # Total worked hours till date (approved only)
        till_date_hours_qs = EmployeeTimesheet.objects.filter(
            date__range=(effective_start_date, today),
            employee_code__employee_code=employee_code,
            status='approved'
        ).aggregate(total=Sum('worked_hours'))

        till_date_hours = till_date_hours_qs['total']
        if isinstance(till_date_hours, timedelta):
            total_utilization_till_date = till_date_hours.total_seconds() / 3600
        elif isinstance(till_date_hours, (int, float)):
            total_utilization_till_date = float(till_date_hours)
        elif isinstance(till_date_hours, str):
            try:
                total_utilization_till_date = float(till_date_hours)
            except ValueError:
                total_utilization_till_date = 0.0
        else:
            total_utilization_till_date = 0.0

        percentage_till_date = (total_utilization_till_date / target_utilization_till_date * 100) if target_utilization_till_date else 0.0

        employee_details = {
            "name": employee.name if employee and employee.name else "N/A",
            "band": employee.band_grade if employee and employee.band_grade else "N/A",
            "reportingManager": employee.manager if employee and employee.manager else "N/A",
            "joiningDate": employee.joining_date.strftime("%Y-%m-%d") if employee and employee.joining_date else "",
            "department":employee.department if employee and employee.department else "N/A"
        }


        return Response({
            'employeeDetails': employee_details,
            'tableData': {
                'targetUtilization': f"{target_utilization} hours",
                'utilization': f"{total_worked_hours:.2f} hours",
                'totalUtilization': f"{utilization_percentage:.2f}%",
                'targetUtilizationTillDate': f"{target_utilization_till_date} hours",
                'totalUtilizationTillDate': f"{percentage_till_date:.2f}%"
            },
            'meterData': {
                'percentage': meter_percentage,
                'percentageTillDate': round(percentage_till_date, 2)
            },
            'chartData': {
                'labels': chart_labels,
                'data': chart_data
            },
            'pendingData': pending_data
        })

    def calculate_working_days(self, start_date, end_date):
        day_count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Mon-Fri
                day_count += 1
            current += timedelta(days=1)
        return day_count

#manager dashboard
class ManagerDashboard(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # --- Helper utilities -------------------------------------------------
    def parse_hours_value(self, value):
        """
        Convert various stored worked_hours formats to float hours.
        Accepts: timedelta, numeric, "HH:MM", "H:MM:SS", or numeric-as-string.
        """
        if value is None:
            return 0.0
        if isinstance(value, timedelta):
            return round(value.total_seconds() / 3600, 2)
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        # numeric string
        if s.replace('.', '', 1).isdigit():
            try:
                return float(s)
            except:
                pass
        parts = s.split(':')
        try:
            if len(parts) == 2:
                h, m = int(parts[0]), int(parts[1])
                return round(h + m/60, 2)
            if len(parts) == 3:
                h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
                return round(h + m/60 + sec/3600, 2)
        except:
            return 0.0
        return 0.0

    def get_working_days(self, start, end):
        """Return list of working dates (Mon-Fri) between start and end inclusive."""
        days = []
        current = start
        while current <= end:
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days

    # --- Core missed entries computation (Option C) ----------------------
    def compute_missed_entries_for_employee(self, employee, project, today=None, cutoff_date=date(2025, 4, 1)):
        """
        Compute missed entries for a specific employee on a specific project.
        Option C semantics:
          - If internal project has >= 8 hours on a date, treat that date as filled for all projects.
          - Otherwise, a project date is missed if project_hours < expected_hours (allocation% * 8).
        """
        if today is None:
            today = date.today()

        # 1. Fetch ProjectTeam entries for the employee & this project
        project_team_entries = ProjectTeam.objects.filter(
            employee_code=employee,
            project_code=project
        ).select_related('task')

        if not project_team_entries.exists():
            return 0

        # 2. Determine employee-specific phase window (min start, max end)
        min_phase_start = min([p.start_date for p in project_team_entries])
        max_phase_end = max([(p.end_date or today) for p in project_team_entries])

        # 3. Effective date window: include cutoff, joining date, phase window
        effective_start = max(employee.joining_date, min_phase_start, cutoff_date)
        effective_end = min(today, max_phase_end)
        if effective_start > effective_end:
            return 0

        # 4. Working dates for this employee-project window
        working_dates = self.get_working_days(effective_start, effective_end)
        if not working_dates:
            return 0

        # 5. Determine expected hours per working day for the project for this employee
        allocation_obj = ProjectTeamAllocation.objects.filter(
            employee_code=employee,
            project_code=project
        ).first()
        allocation_percent = allocation_obj.allocation_percent if allocation_obj else 0.0
        expected_hours = round((allocation_percent / 100.0) * 8.0, 2)

        # 6. Identify internal project (single project whose description is 'Internal Project')
        internal_obj = Project.objects.filter(project_description__iexact="internal project").first()
        internal_project_code = internal_obj.project_code if internal_obj else None

        # 7. Load timesheets for this employee + project in the window (approved/open)
        ts_qs = EmployeeTimesheet.objects.filter(
            employee_code=employee,
            project_code=project,
            date__range=(effective_start, effective_end),
            status__in=['approved', 'open']
        )

        worked_by_date = defaultdict(float)
        for t in ts_qs:
            hrs = self.parse_hours_value(t.worked_hours)
            worked_by_date[t.date] += hrs

        # 8. If we have an internal project, load internal hours for this employee (approved/open)
        internal_hours_by_date = defaultdict(float)
        if internal_project_code:
            internal_ts = EmployeeTimesheet.objects.filter(
                employee_code=employee,
                project_code__project_code=internal_project_code,
                date__range=(effective_start, effective_end),
                status__in=['approved', 'open']
            )
            for t in internal_ts:
                hrs = self.parse_hours_value(t.worked_hours)
                internal_hours_by_date[t.date] += hrs

        # 9. Count missed dates according to Option C
        missed = 0
        for d in working_dates:
            # If internal project has >= 8 hrs on this date, treat as filled for all projects
            if internal_project_code and internal_hours_by_date.get(d, 0.0) >= 8.0:
                continue

            project_hours = round(worked_by_date.get(d, 0.0), 2)
            if project_hours < expected_hours:
                missed += 1

        return missed

    # --- Main GET view --------------------------------------------------
    def get(self, request, project_code):
        try:
            project = Project.objects.get(project_code=project_code)
            allocated = ProjectTeam.objects.filter(project_code=project).aggregate(total=Sum("allocated_hours"))["total"] or 0

            # Calculate total worked hours for entire project (approved only)
            total_worked_timedelta = EmployeeTimesheet.objects.filter(
                project_code=project, status='approved'
            ).aggregate(total=Sum('worked_hours'))['total'] or timedelta()

            total_seconds = total_worked_timedelta.total_seconds()
            total_hours = int(total_seconds // 3600)
            total_minutes = int((total_seconds % 3600) // 60)
            worked_str = f"{total_hours:02d}:{total_minutes:02d}"

            total_worked_hours = total_seconds / 3600.0
            utilization = round(total_worked_hours / float(allocated) * 100, 2) if allocated > 0 else 0.0

            phases = PhaseAllocation.objects.filter(project_code=project)

            # Prepare a list of tuples with (label, allocated_hours, worked_hours)
            phase_data = []
            for phase in phases:
                phase_worked_timedelta = EmployeeTimesheet.objects.filter(
                    project_code=project,
                    task_description=phase.task,
                    status='approved'
                ).aggregate(total=Sum('worked_hours'))['total'] or timedelta()

                phase_worked_seconds = phase_worked_timedelta.total_seconds()
                phase_worked_hours = round(phase_worked_seconds / 3600, 2)

                label = phase.task.task_group
                phase_data.append((label, phase.allocated_hours, phase_worked_hours))

            # Sort phase data and unpack
            phase_data.sort(key=lambda x: x[0])
            phase_labels = [x[0] for x in phase_data]
            phase_allocated = [x[1] for x in phase_data]
            phase_worked = [x[2] for x in phase_data]

            # Get unique employees assigned to project
            employee_codes = ProjectTeam.objects.filter(project_code=project).values_list('employee_code', flat=True).distinct()

            emp_utilization_data = []
            for emp_code in employee_codes:
                employee = Employee.objects.filter(employee_code=emp_code).first()
                employee_name = employee.name if employee else ""

                total_allocated = ProjectTeam.objects.filter(
                    employee_code=emp_code, project_code=project
                ).aggregate(total=Sum("allocated_hours"))["total"] or 0

                total_worked_emp = EmployeeTimesheet.objects.filter(
                    employee_code=emp_code, project_code=project, status="approved"
                ).aggregate(total=Sum("worked_hours"))["total"] or timedelta()

                total_worked_emp_hours = round(total_worked_emp.total_seconds() / 3600, 2) if total_worked_emp else 0.0

                emp_util = round(total_worked_emp_hours / float(total_allocated) * 100, 2) if total_allocated > 0 else 0.0

                # Compute till_allocated_hours using unique working days between assignment windows & today
                today = date.today()
                assignments = ProjectTeam.objects.filter(employee_code=emp_code, project_code=project)
                working_days_set = set()
                for assign in assignments:
                    start_date = assign.start_date
                    end_date = assign.end_date if assign.end_date and assign.end_date <= today else today
                    if start_date > end_date:
                        continue
                    cur = start_date
                    while cur <= end_date:
                        if cur.weekday() < 5:
                            working_days_set.add(cur)
                        cur += timedelta(days=1)

                allocation_obj = ProjectTeamAllocation.objects.filter(
                    employee_code=emp_code,
                    project_code=project
                ).first()
                allocation_percent = allocation_obj.allocation_percent if allocation_obj else 0.0

                till_allocated_hours = len(working_days_set) * (allocation_percent / 100.0) * 8.0
                till_utilization = round((total_worked_emp_hours / till_allocated_hours) * 100, 2) if till_allocated_hours else 0.0

                emp_utilization_data.append({
                    "project_code": project_code,
                    "project_name": project.project_description,
                    "employee_code": emp_code,
                    "employee_name": employee_name,
                    "total_allocated_hours": total_allocated,
                    "total_worked_hours": total_worked_emp_hours,
                    "utilization": emp_util,
                    "allocation_percent": allocation_percent,
                    "till_allocated_hours": round(till_allocated_hours, 2),
                    "till_utilization": round(till_utilization, 2)
                })

            # Build time_log_data using the unified compute_missed_entries_for_employee
            time_log_data = []
            employees = ProjectTeam.objects.filter(project_code=project).values_list("employee_code", flat=True).distinct()
            for emp_code in employees:
                employee = Employee.objects.get(employee_code=emp_code)
                missed = self.compute_missed_entries_for_employee(employee, project)
                time_log_data.append({
                    "project_code": project.project_code,
                    "project_name": project.project_description,
                    "employee_code": emp_code,
                    "employee_name": employee.name,
                    "missed_entries": missed
                })

            response_data = {
                "tableData": {
                    "total_allocated_hours": allocated,
                    "worked_hours": worked_str,
                    "Utilization": str(utilization)
                },
                "meterdata": {
                    "percentage": utilization
                },
                "chartData": {
                    "allocated_hours": [project.allocated_hours] if project.project_code == "RB001" else phase_allocated,
                    "worked_hours": phase_worked,
                    "labels": phase_labels
                },
                "emp_utilization": emp_utilization_data,
                "time_log_data": time_log_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

# --- Asset Categories-----

# --- Create Asset Category ---
@swagger_auto_schema(
    method='post',
    request_body=AssetCategoriesSerializer,
    operation_description="Create a new asset category (Hardware/Software with category and sub-category).",
    responses={
        201: openapi.Response(description="Asset category created", schema=AssetCategoriesSerializer),
        400: "Bad request"
    }
)
@api_view(['POST'])
def create_asset_category(request):
    serializer = AssetCategoriesSerializer(data=request.data)

    if serializer.is_valid():
        asset = serializer.save()  
        return Response(
            {
                "message": "Asset category created successfully.",
                "data": AssetCategoriesSerializer(asset).data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]

    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all asset categories.",
    responses={200: openapi.Response(description="List of asset categories", schema=AssetCategoriesSerializer(many=True))}
)
@api_view(['GET'])
def get_all_asset_categories(request):
    assets = AssetCategories.objects.all()
    serializer = AssetCategoriesSerializer(assets, many=True)
    return Response({
        "message": "Asset categories retrieved successfully.",
        "data": serializer.data
    })

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a single asset category by ID.",
    responses={200: openapi.Response(description="Asset category details", schema=AssetCategoriesSerializer),
               404: "Not found"}
)
@api_view(['GET'])
def get_asset_category_by_id(request, asset_id):
    try:
        asset_category = AssetCategories.objects.get(asset_id=asset_id)
        serializer = AssetCategoriesSerializer(asset_category)
        return Response({
            "message": "Asset category retrieved successfully.",
            "data": serializer.data
        })
    except AssetCategories.DoesNotExist:
        return Response({"message": "Asset category not found."}, status=404)

@swagger_auto_schema(
    method='put',
    request_body=AssetCategoriesSerializer,
    operation_description="Update an existing asset category by ID.",
    responses={
        200: openapi.Response(description="Asset category updated", schema=AssetCategoriesSerializer),
        400: "Bad request",
        404: "Not found"
    }
)
@api_view(['PUT'])
def update_asset_category(request, asset_id):
    try:
        asset = AssetCategories.objects.get(asset_id=asset_id)
    except AssetCategories.DoesNotExist:
        return Response(
            {"message": "Asset category not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AssetCategoriesSerializer(asset, data=request.data, partial=True)
    if serializer.is_valid():
        updated_asset = serializer.save()
        return Response(
            {
                "message": "Asset category updated successfully.",
                "data": AssetCategoriesSerializer(updated_asset).data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='delete',
    operation_description="Delete an asset category by ID."
)
@api_view(['DELETE'])
def delete_asset_category(request, asset_id):
    try:
        asset = AssetCategories.objects.get(asset_id=asset_id)
    except AssetCategories.DoesNotExist:
        return Response({"message": "Asset category not found."}, status=status.HTTP_404_NOT_FOUND)


    asset.delete()
    return Response({"message": "Asset category deleted successfully."}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'asset_type',
            openapi.IN_QUERY,
            description="Asset type to filter by (e.g., 'hardware', 'software'). If not provided, returns all categories.",
            type=openapi.TYPE_STRING,
            required=False
        )
    ],
    operation_description="Retrieve asset categories grouped by category with sub-categories, optionally filtered by asset type.",
    responses={200: openapi.Response(description="Grouped asset categories")}
)
@api_view(['GET'])
def get_grouped_asset_categories(request):
    """
    Returns asset categories grouped by category with sub-categories
    Optional: Filter by asset_type parameter
    Format: [{"cat1": [{"name": "sub cat1"}, {"name": "sub cat2"}]}, ...]
    """
    try:
        # Get the asset_type filter from query parameters
        asset_type = request.query_params.get('asset_type')
        
        # Build the base queryset
        categories_query = AssetCategories.objects.all()
        
        # Apply asset_type filter if provided
        if asset_type:
            categories_query = categories_query.filter(asset_type__iexact=asset_type.strip())
        
        # Get all distinct category and sub-category pairs
        categories_data = categories_query.values(
            category=F('asset_category'),
            sub_category=F('asset_sub_category')
        ).distinct().order_by('asset_category', 'asset_sub_category')
        
        # Group sub-categories by category
        grouped_dict = defaultdict(list)
        
        for item in categories_data:
            category = item['category']
            sub_category = item['sub_category']
            
            if category and sub_category:  # Only add if both are not empty
                grouped_dict[category].append({"name": sub_category})
        
        # Convert to the required format
        result = []
        for category, sub_categories in sorted(grouped_dict.items()):
            if sub_categories:  # Only add categories that have sub-categories
                result.append({category: sub_categories})
        
        # Prepare response message
        if asset_type:
            message = f"Asset categories for '{asset_type}' retrieved successfully (grouped by category)."
        else:
            message = "All asset categories retrieved successfully (grouped by category)."
        
        return Response({
            "message": message,
            "asset_type_filter": asset_type if asset_type else "all",
            "data": result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "message": "Failed to retrieve grouped asset categories.",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method='post',
    request_body=AssetModelSerializer,
    operation_description="Create a new asset model (with code and name).",
    responses={
        201: openapi.Response(description="Asset model created", schema=AssetModelSerializer),
        400: "Bad request"
    }
)
@api_view(['POST'])
def create_asset_model(request):
    serializer = AssetModelSerializer(data=request.data)

    if serializer.is_valid():
        asset = serializer.save()
        return Response(
            {
                "message": "Asset model created successfully.",
                "data": AssetModelSerializer(asset).data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all asset models.",
    responses={200: openapi.Response("List of asset models", AssetModelSerializer(many=True))}
)
@api_view(['GET'])
def get_all_asset_models(request):
    assets = AssetModel.objects.all()
    serializer = AssetModelSerializer(assets, many=True)
    return Response({
        "message": "Asset models retrieved successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a single asset model by its ID (e.g., AM1, AM2...).",
    responses={200: AssetModelSerializer, 404: "Not found"}
)
@api_view(['GET'])
def get_asset_model_by_id(request, asset_model_id):
    try:
        asset = AssetModel.objects.get(asset_model_id=asset_model_id)
        serializer = AssetModelSerializer(asset)
        return Response({
            "message": "Asset model retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except AssetModel.DoesNotExist:
        return Response({"message": "Asset model not found."}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='put',
    request_body=AssetModelSerializer,
    operation_description="Update an existing asset model by ID (e.g., AM1, AM2...).",
    responses={
        200: openapi.Response(description="Asset model updated", schema=AssetModelSerializer),
        400: "Bad request",
        404: "Not found"
    }
)
@api_view(['PUT'])
def update_asset_model(request, asset_model_id):
    try:
        asset = AssetModel.objects.get(asset_model_id=asset_model_id)
    except AssetModel.DoesNotExist:
        return Response(
            {"message": "Asset model not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AssetModelSerializer(asset, data=request.data, partial=True)
    if serializer.is_valid():
        updated_asset = serializer.save()
        return Response(
            {
                "message": "Asset model updated successfully.",
                "data": AssetModelSerializer(updated_asset).data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='delete',
    operation_description="Delete an asset model by ID (e.g., AM1, AM2...)."
)
@api_view(['DELETE'])
def delete_asset_model(request, asset_model_id):
    try:
        asset = AssetModel.objects.get(asset_model_id=asset_model_id)
    except AssetModel.DoesNotExist:
        return Response({"message": "Asset model not found."}, status=status.HTTP_404_NOT_FOUND)


    asset.delete()
    return Response({"message": "Asset model deleted successfully."}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='post',
    request_body=StatusSerializer,
    operation_description="Create a new status.",
    responses={
        201: openapi.Response(description="Status created", schema=StatusSerializer),
        400: "Bad request"
    }
)
@api_view(['POST'])
def create_status(request):
    serializer = StatusSerializer(data=request.data)

    if serializer.is_valid():
        status_obj = serializer.save()
        return Response(
            {
                "message": "Status created successfully.",
                "data": StatusSerializer(status_obj).data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all statuses.",
    responses={
        200: openapi.Response(
            "List of statuses",
            StatusSerializer(many=True)
        )
    }
)
@api_view(['GET'])
def get_all_status(request):
    statuses = Status.objects.all()
    serializer = StatusSerializer(statuses, many=True)
    return Response({
        "message": "Statuses retrieved successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a single status by its ID (e.g., ST1, ST2...).",
    responses={
        200: StatusSerializer,
        404: openapi.Response(
            "Not found",
            examples={
                "application/json": {"message": "Status not found."}
            }
        )
    }
)
@api_view(['GET'])
def get_status_by_id(request, status_id):
    try:
        status_obj = Status.objects.get(status_id=status_id)
        serializer = StatusSerializer(status_obj)
        return Response({
            "message": "Status retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Status.DoesNotExist:
        return Response({"message": "Status not found."}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='put',
    request_body=StatusSerializer,
    operation_description="Update an existing status.",
    responses={
        200: openapi.Response(description="Status updated", schema=StatusSerializer),
        400: "Bad request",
        404: "Not found"
    }
)
@api_view(['PUT'])
def update_status(request, status_id):
    try:
        status_obj = Status.objects.get(status_id=status_id)
    except Status.DoesNotExist:
        return Response(
            {"message": "Status not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = StatusSerializer(status_obj, data=request.data, partial=True)
    if serializer.is_valid():
        updated_status = serializer.save()
        return Response(
            {
                "message": "Status updated successfully.",
                "data": StatusSerializer(updated_status).data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method='delete',
    operation_description="Delete a status by ID (e.g., ST1, ST2...).",
    responses={
        200: openapi.Response(
            "Status deleted successfully",
            examples={"application/json": {"message": "Status deleted successfully."}}
        ),
        404: openapi.Response(
            "Not found",
            examples={"application/json": {"message": "Status not found."}}
        )
    }
)
@api_view(['DELETE'])
def delete_status(request, status_id):
    try:
        status_obj = Status.objects.get(status_id=status_id)
    except Status.DoesNotExist:
        return Response({"message": "Status not found."}, status=status.HTTP_404_NOT_FOUND)


    status_obj.delete()
    return Response({"message": "Status deleted successfully."}, status=status.HTTP_200_OK)


# ---------------- COMPANY ----------------
# List Companies
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all companies",
    responses={
        200: openapi.Response(
            description="List of companies",
            schema=CompanySerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_companies(request):
    companies = Company.objects.all()
    serializer = CompanySerializer(companies, many=True)
    return Response({"message": "Companies retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a company by ID",
    responses={
        200: openapi.Response(
            description="Company retrieved successfully",
            schema=CompanySerializer()
        ),
        404: "Company not found"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_company(request, key):
    try:
        company = Company.objects.get(id=key)
        serializer = CompanySerializer(company)
        return Response({"message": "Company retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    except Company.DoesNotExist:
        return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)


# Create Company
@swagger_auto_schema(
    method='post',
    request_body=CompanySerializer,
    responses={
        201: openapi.Response(
            description="Company created successfully",
            schema=CompanySerializer()
        ),
        400: "Bad Request"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_company(request):
    serializer = CompanySerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Company created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )


# Get Company by ID
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a company by its ID",
    responses={
        200: openapi.Response(
            description="Company retrieved successfully",
            schema=CompanySerializer()
        ),
        404: "Company not found"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_company_by_id(request, key):
    try:
        company = Company.objects.get(id=key)
        serializer = CompanySerializer(company)
        return Response({"message": "Company retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    except Company.DoesNotExist:
        return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)


# Update Company
@swagger_auto_schema(
    method='put',
    request_body=CompanySerializer,
    responses={
        200: openapi.Response(
            description="Company updated successfully",
            schema=CompanySerializer()
        ),
        400: "Validation error",
        404: "Company not found"
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_company(request, key):
    try:
        company = Company.objects.get(id=key)
    except Company.DoesNotExist:
        return Response(
            {"message": "Company not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    updated_data = {}
    for field in CompanySerializer.Meta.fields:
        if field in ['id', 'created_at', 'updated_at']:
            continue
        value = request.data.get(field, None)
        if value in [None, "", "string"]:
            updated_data[field] = getattr(company, field)
        else:
            updated_data[field] = value

    serializer = CompanySerializer(company, data=updated_data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Company updated successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )


# Delete Company
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a company by ID",
    responses={
        204: "Company deleted successfully",
        404: "Company not found"
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_company(request, key):
    try:
        company = Company.objects.get(id=key)
        company.delete()
        return Response({"message": "Company deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Company.DoesNotExist:
        return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)


# ---------------- SUPPLIER ----------------
# List Suppliers
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all suppliers",
    responses={
        200: openapi.Response(
            description="List of suppliers",
            schema=SupplierSerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_suppliers(request):
    suppliers = Supplier.objects.all()
    serializer = SupplierSerializer(suppliers, many=True)
    return Response({"message": "Suppliers retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)


# Create Supplier
@swagger_auto_schema(
    method='post',
    request_body=SupplierSerializer,
    responses={
        201: openapi.Response(
            description="Supplier created successfully",
            schema=SupplierSerializer()
        ),
        400: "Bad Request"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_supplier(request):
    serializer = SupplierSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Supplier created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )

# Get Supplier by ID
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a supplier by ID",
    responses={
        200: openapi.Response(
            description="Supplier retrieved successfully",
            schema=SupplierSerializer()
        ),
        404: "Supplier not found"
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_supplier(request, key):
    try:
        supplier = Supplier.objects.get(id=key)
        serializer = SupplierSerializer(supplier)
        return Response({"message": "Supplier retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)
    except Supplier.DoesNotExist:
        return Response({"message": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)


# Update Supplier
@swagger_auto_schema(
    method='put',
    request_body=SupplierSerializer,
    responses={
        200: openapi.Response(
            description="Supplier updated successfully",
            schema=SupplierSerializer()
        ),
        400: "Validation error",
        404: "Supplier not found"
    }
)
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_supplier(request, key):
    try:
        supplier = Supplier.objects.get(id=key)
    except Supplier.DoesNotExist:
        return Response(
            {"message": "Supplier not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    updated_data = {}
    for field in SupplierSerializer.Meta.fields:
        if field in ['id', 'created_at', 'updated_at']:
            continue
        value = request.data.get(field, None)
        if value in [None, "", "string"]:
            updated_data[field] = getattr(supplier, field)
        else:
            updated_data[field] = value

    serializer = SupplierSerializer(supplier, data=updated_data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Supplier updated successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    error_message = next(iter(serializer.errors.values()))[0]
    return Response(
        {"message": error_message},
        status=status.HTTP_400_BAD_REQUEST
    )


# Delete Supplier
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a supplier by ID",
    responses={
        204: "Supplier deleted successfully",
        404: "Supplier not found"
    }
)
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_supplier(request, key):
    try:
        supplier = Supplier.objects.get(id=key)
        supplier.delete()
        return Response({"message": "Supplier deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Supplier.DoesNotExist:
        return Response({"message": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)
    

#get all companies

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_companies_with_locations(request):
    """
    Retrieve all companies with their locations in the required format:
    [
        {"Company Name": [{"name": "Location1"}, {"name": "Location2"}]},
        ...
    ]
    """
    companies = Company.objects.all()
    response_data = []

    for company in companies:
        locations = [{"name": loc} for loc in company.location_name]  # convert list of strings to list of dicts
        response_data.append({company.company: locations})

    return Response(response_data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Display employees based on active/inactive filter.",
    manual_parameters=[
        openapi.Parameter(
            name='is_active',
            in_=openapi.IN_QUERY,
            description="true → active, false → inactive, empty → all",
            type=openapi.TYPE_BOOLEAN,
            required=False
        )
    ],
    responses={
        200: openapi.Response(
            "Employees retrieved successfully.",
            EmployeeSerializer(many=True)
        )
    }
)
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def display_name(request):

    is_active_param = request.query_params.get("is_active")

    if is_active_param is None:
        employees = Employee.objects.all()
    else:
        is_active = str(is_active_param).lower() in {"true", "1", "yes"}

        if is_active:
            employees = Employee.objects.filter(status__in=["Active", "active"])
        else:
            employees = Employee.objects.filter(status__in=["Inactive", "inactive"])

    emp_codes = employees.values_list("employee_code", flat=True)
    user_profiles = UserProfile.objects.filter(user_id__in=emp_codes)
    role_assignments = UserRoleAssign.objects.filter(user_id__in=user_profiles)

    role_map = {}
    for r in role_assignments:
        role_map.setdefault(r.user_id.user_id, set()).update(r.role_name)

    response_data = []
    for emp in employees:
        emp_data = EmployeeSerializer(emp).data
        emp_data["roles"] = list(role_map.get(emp.employee_code, []))
        response_data.append(emp_data)

    return Response({"data": response_data}, status=status.HTTP_200_OK)