from rest_framework import status
from django.utils.html import strip_tags
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserProfile, UserRoleAssign,Roles
from master_data.models import Employee
from .serializers import UserCreateSerializer, UserEditSerializer, UserListSerializer
from .serializers import UserRoleAssignSerializer, UserRoleAssignListSerializer,RolesSerializer,EditUserRoleAssignSerializer
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import logging
from pmo.models import Project,ProjectTeam,ProjectRoles,ProjectTasks
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes


# def generate_random_password(length=12):

#     length = max(6, min(length, 12))
#     # Ensure minimum components
#     uppercase = random.choice(string.ascii_uppercase)
#     lowercase = random.choice(string.ascii_lowercase)
#     digit = random.choice(string.digits)
#     special = random.choice("!@#$%^&*(),.?\":{}|<>")
    
#     # Fill the rest randomly
#     others = random.choices(string.ascii_letters + string.digits + "!@#$%^&*(),.?\:{}|<>", k=length - 4)
    
#     # Combine and shuffle
#     password_list = list(uppercase + lowercase + digit + special + ''.join(others))
#     random.shuffle(password_list)
    
#     return ''.join(password_list)

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


# Set up logger
logger = logging.getLogger(__name__) 
# #create user
# @swagger_auto_schema(
#     method='post',
#     operation_description="Create a new user from an existing employee.",
#     request_body=UserCreateSerializer,
#     responses={
#         201: openapi.Response("User created successfully!", UserCreateSerializer),
#         400: "Bad Request - Validation errors."
#     }
# )
# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def create_user(request):
#     """
#     Create a new user from an existing employee record.
#     """
#     data = request.data

#     # 1. Check if Employee with given user_id exists
#     employee_code = data.get('user_id')
#     try:
#         employee = Employee.objects.get(employee_code=employee_code)
#     except Employee.DoesNotExist:
#         return Response({'error': 'Employee with this employee_code not found.'}, status=status.HTTP_400_BAD_REQUEST)

#     # 2. Check if User already exists
#     if UserProfile.objects.filter(user_id=employee_code).exists():
#         return Response({'error': 'User with this user_id already exists.'}, status=status.HTTP_400_BAD_REQUEST)

#     if UserProfile.objects.filter(email=data.get('email')).exists():
#         return Response({'error': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

#     # 3. Validate data
#     required_fields = ['name', 'password', 'email', 'mobile', 'start_date', 'end_date', 'status']
#     if any(not data.get(field) for field in required_fields):
#         return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

#     # 4. Manually set user_id to match employee_code
#     data['user_id'] = employee_code

#     # Serialize the user data and create the user
#     serializer = UserCreateSerializer(data=data)
#     if serializer.is_valid():
#         user = serializer.save()
    
#     if employee.name != "Sudhakara Varma Yarramraju":
#     #     # STEP 1: Assign default project (RB001) to the user
#         try:
#             default_project = Project.objects.get(project_code='RB001')
#         except Project.DoesNotExist:
#             return Response({"error": "Default project 'RB001' not found."}, status=status.HTTP_400_BAD_REQUEST)
        
#         task_obj = ProjectTasks.objects.filter(task_group="Organization Standard Tasks").first()
#         if not task_obj:
#             return Response({"error": "Task 'Organization Standard Tasks' not found."}, status=status.HTTP_400_BAD_REQUEST)

#         # STEP 2: Create entry in ProjectTeam for the user
#         # start_date = timezone.now().date()  # Get current date for start_date
#         start_date = employee.joining_date
#         ProjectTeam.objects.create(
#             project_code=default_project,
#             employee_code=employee,
#             employee_name=employee.name,
#             designation=employee.designation,
#             project_role=ProjectRoles.objects.first(),  # Assuming a default project role is set
#             start_date=start_date,  # Use dynamic start date
#             end_date="2125-12-31",  # Set a long default end date
#             task=task_obj,
#             allocated_hours=10000
#         )

#         # STEP 3: Get email from UserProfile
#         email = data.get('email')  # Get the email from the request data

#         # STEP 4: Fetch all projects assigned to this user
#         assigned_projects = ProjectTeam.objects.filter(employee_code=employee)

#         # STEP 5: Build HTML email content
#         project_details_html = ""
#         for proj in assigned_projects:
#             project_details_html += f"""
#                 <p><strong>Project:</strong> {proj.project_code.project_description}<br>
#                 <strong>Project Code:</strong> {proj.project_code.project_code}</p>
#             """

#         html_message = f"""
#             <p>Hi {employee.name},</p>
#             <p>You have been assigned to the following project:</p>
#             {project_details_html}
#             <p>Best regards,<br><strong>ROBOXA PMO.</strong></p>
#         """
#         # Plain text fallback
#         plain_message = strip_tags(html_message)

#         # STEP 6: Send email if email is available
#         if email:
#             email_msg = EmailMultiAlternatives(
#                 subject="Project Assignment Notification",
#                 body=plain_message,
#                 from_email=settings.EMAIL_HOST_USER,
#                 to=[email]
#             )
#             email_msg.attach_alternative(html_message, "text/html")
#             email_msg.send()

#         # Log user creation and project assignment
#         logger.info(f"User {user.user_id} created and assigned to default project 'RB001'.")

#         response_data = {
#             'message': 'User created successfully!',
#             'user': UserListSerializer(user).data
#         }
#         response_data['user'].pop('password', None)

#         return Response(response_data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#create user
@swagger_auto_schema(
    method='post',
    operation_description="Create a new user from an existing employee.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["user_id", "name", "email", "mobile", "start_date", "end_date", "status"],
        properties={
            "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
            "name": openapi.Schema(type=openapi.TYPE_STRING),
            "email": openapi.Schema(type=openapi.TYPE_STRING, format='email'),
            "mobile": openapi.Schema(type=openapi.TYPE_STRING),
            "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
            "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date"),
            "status": openapi.Schema(type=openapi.TYPE_STRING)
            # Note: No 'password' field here
        }
    ),
    responses={201: "User created"}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_user(request):
    data = request.data.copy()
    employee_code = data.get('user_id')

    # Step 1: Validate employee
    try:
        employee = Employee.objects.get(employee_code=employee_code)
    except Employee.DoesNotExist:
        return Response({'error': 'Employee with this employee_code not found.'}, status=status.HTTP_400_BAD_REQUEST)

    # Step 2: Check for duplicate users
    if UserProfile.objects.filter(user_id=employee_code).exists():
        return Response({'error': 'User with this user_id already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    if UserProfile.objects.filter(email=data.get('email')).exists():
        return Response({'error': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Step 3: Check required fields
    required_fields = ['name', 'email', 'mobile', 'start_date', 'end_date', 'status']
    if any(not data.get(field) for field in required_fields):
        return Response({'error': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Step 4: Handle password
    autogenerated_password = None
    if not data.get('password'):
        autogenerated_password = generate_random_password()
        data['password'] = autogenerated_password

    # Step 5: Serialize and create
    data['user_id'] = employee_code
    serializer = UserCreateSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(data['password'])
        user.change_password_required = True 
        user.save()

        # Assign to default project if not "Sudhakara Varma Yarramraju"
        if employee.name != "Sudhakara Varma Yarramraju":
            try:
                default_project = Project.objects.get(project_code='RB001')
                task_obj = ProjectTasks.objects.filter(task_group="Organization Standard Tasks").first()
                ProjectTeam.objects.create(
                    project_code=default_project,
                    employee_code=employee,
                    employee_name=employee.name,
                    designation=employee.designation,
                    project_role=ProjectRoles.objects.first(),
                    start_date=employee.joining_date,
                    end_date="2125-12-31",
                    task=task_obj,
                    allocated_hours=10000
                )
            except Exception as e:
                logger.warning(f"Project assignment failed: {e}")

        # Send welcome email
        assigned_projects = ProjectTeam.objects.filter(employee_code=employee)
        project_details_html = "".join([
            f"<p><strong>Project:</strong> {proj.project_code.project_description}<br>"
            f"<strong>Project Code:</strong> {proj.project_code.project_code}</p>"
            for proj in assigned_projects
        ])
        html_message = f"""
            <p>Hi {employee.name},</p>
            <p>You have been assigned to the following project(s):</p>
            {project_details_html}
            <p>Best regards,<br><strong>ROBOXA PMO</strong></p>
        """


        plain_message = strip_tags(html_message)
        if data.get('email'):
            email_msg = EmailMultiAlternatives(
                subject="Project Assignment Notification",
                body=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                to=[data.get('email')]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send()

        logger.info(f"User {user.user_id} created.")

        response_data = {
            'message': 'User created successfully!',
            'user': UserListSerializer(user).data
        }
        response_data['user'].pop('password', None)
        # if autogenerated_password:
        #     response_data['generated_password'] = autogenerated_password
        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#get user by id
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a user by their ID.",
    responses={200: openapi.Response("User details.", UserListSerializer)}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_by_id(request, user_id):
    try:
        user = UserProfile.objects.get(user_id=user_id)
        serializer = UserListSerializer(user)
        response_data = serializer.data
        # userprofile = LoginHistory.objects.get(user_id=user_id)
        # created_on = userprofile.created_on
        # response_data['last_login'] = created_on
    except User.DoesNotExist:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"user": response_data}, status=status.HTTP_200_OK)

#maintain users
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all users with their roles.",
    responses={200: openapi.Response("List of users with roles.", UserListSerializer(many=True))}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def maintain_users(request):
    """
    Retrieve a list of all users with their profile details and assigned roles.
    """
    profiles = UserProfile.objects.all()
    serializer = UserListSerializer(profiles, many=True)

    response_data = serializer.data
    for profile_data in response_data:
        user_id = profile_data['user_id']
        
        # Fetch role names correctly
        user_roles = UserRoleAssign.objects.filter(user_id=user_id).values_list('role_name', flat=True)

        # Convert role_name from `{PMO,Employee}` -> ["PMO", "Employee"]
        formatted_roles = []
        for role in user_roles:
            if isinstance(role, str) and role.startswith("{") and role.endswith("}"):
                formatted_roles.extend(role.strip("{}").split(",")) 
            elif isinstance(role, list):
                formatted_roles.extend(role) 
            else:
                formatted_roles.append(role)

        profile_data['role_name'] = formatted_roles if formatted_roles else None  

    return Response({'users': response_data}, status=status.HTTP_200_OK)


# #edit user
@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing user's details.",
    request_body=UserEditSerializer,
    responses={
        200: openapi.Response("User updated successfully!", UserEditSerializer),
        404: "Not Found - User not found.",
        400: "Bad Request - Validation errors."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_user(request, user_id):
    try:
        user = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()

    # Check if email is being changed
    new_email = data.get('email')
    email_changed = new_email and user.email != new_email

    # 1.  Prevent duplicate email
    if email_changed and UserProfile.objects.filter(email=new_email).exclude(user_id=user_id).exists():
        return Response({'error': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # 2.  Always generate new password if email is changed
    auto_generated_password = None
    if email_changed or not data.get('password'):
        auto_generated_password = generate_random_password()
        data['password'] = auto_generated_password

    serializer = UserEditSerializer(user, data=data, partial=True)
    if serializer.is_valid():
        updated_user = serializer.save()

        # Set new hashed password
        updated_user.set_password(data['password'])
        updated_user.change_password_required = True
        updated_user.save()

        # 3.  Update UserRoleAssign if present
        try:
            user_role_assign = UserRoleAssign.objects.get(user_id=user_id)
            user_role_assign.status = data.get('status', user_role_assign.status)
            user_role_assign.email = new_email or user_role_assign.email
            user_role_assign.name = data.get('name', user_role_assign.name)
            user_role_assign.start_date = data.get('start_date', user_role_assign.start_date)
            user_role_assign.end_date = data.get('end_date', user_role_assign.end_date)
            user_role_assign.mobile = data.get('mobile', user_role_assign.mobile)
            user_role_assign.save()
        except UserRoleAssign.DoesNotExist:
            pass

        # 4.  Send new credentials if email changed
        if email_changed and new_email:
            subject = "Your PMO Account Credentials"
            plain_message = f"""
Hi {user.name},

Your account has been successfully created. Below are your login credentials:

Your new credentials:
Email: {new_email}
Password: {auto_generated_password}


Please check the network you are connected to and use the appropriate URL below to access the PMO Application:
If you are connected to the 'Roboxa' network, please use: http://pmo.roboxaservices.com/
If you are connected otherthan 'Roboxa' network (VPN or external network), please use: http://pub-pmo.roboxaservices.com/

Please login and change your password immediately.

- ROBOXA TECHNOLOGIES Pvt Ltd.
"""

            html_message = f"""
<html>
<body>
    <p>Hi {user.name},</p>
    <p>Your login email has been updated. Below are your new credentials:</p>
    <p><strong>Email:</strong> {new_email}<br>
    <strong>Password:</strong> {auto_generated_password}</p>
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

        return Response({
            'message': 'User updated successfully!',
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#delete user
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a user by their UserId.",
    responses={
        200: "User deleted successfully.",
        404: "Not Found - User not found."
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """
    Soft delete a user by setting is_active=False and status='inactive'.
    Also deactivates related role assignments if needed.
    """
    try:
        user = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    # Mark user as inactive
    user.is_active = False
    user.status = 'inactive'
    user.save()

    # Optionally deactivate user roles too (if applicable)
    # try:
    #     role = UserRoleAssign.objects.get(user_id=user_id)
    #     role.status = 'inactive'
    #     role.save()
    # except UserRoleAssign.DoesNotExist:
    #     pass  # No role assigned, nothing to update

    return Response({'message': 'User deleted successfully!'}, status=status.HTTP_200_OK)

# @api_view(['DELETE'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def delete_user(request, user_id):
#     """
#     Delete a user by their ID, ensuring proper handling of non-existent users.
#     """
#     try:    
#         user = UserProfile.objects.get(user_id=user_id)
#     except UserProfile.DoesNotExist:
#         return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#     user.delete()
#     return Response({'message': 'User deleted successfully!'}, status=status.HTTP_200_OK)

# #user role assign
# @swagger_auto_schema(
#     method='post',
#     operation_description="Create or update roles for a user.",
#     request_body=UserRoleAssignSerializer,
#     responses={
#         201: openapi.Response("Roles assigned to user successfully!", UserRoleAssignSerializer),
#         400: "Bad Request - Validation errors.",
#         404: "User not found.",
#         409: "Conflict - User already has roles assigned."
#     }
# )

# @api_view(['POST'])
# @authentication_classes([JWTAuthentication])
# @permission_classes([IsAuthenticated])
# def assign_or_update_user_roles(request):
    
#     user_id = request.data.get('user_id')
#     role_names = request.data.get('role_name', [])

#     # Validate input
#     if not user_id or not role_names:
#         return Response({"error": "Both user_id and role_name are required."}, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         # Check if user already has a role assignment
#         user_role = UserRoleAssign.objects.get(user_id=user_id)

#         # If user exists, update the role_name array
#         user_role.role_name = list(set(user_role.role_name).union(set(role_names)))  # Union to avoid duplicates
#         user_role.save()

#         return Response({
#             "message": "User roles updated successfully!",
#             "data": UserRoleAssignSerializer(user_role).data
#         }, status=status.HTTP_200_OK)

#     except UserRoleAssign.DoesNotExist:
#         # If user does not exist, create a new role assignment
#         try:
#             # Validate if the user exists in the related UserProfile model
#             user = UserProfile.objects.get(user_id=user_id)
#             # Retrieve the user's existing password (ensure it's not hashed)
#             plain_password = user.password  
#         except UserProfile.DoesNotExist:
#             return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

#         # Prepare the data to create a new UserRoleAssign
#         data = {
#             'user_id': user.user_id,  # UserProfile ID
#             'role_name': role_names,
#             'name': request.data.get('name'),
#             'email': request.data.get('email'),
#             'mobile': request.data.get('mobile'),
#             'start_date': request.data.get('start_date'),
#             'end_date': request.data.get('end_date'),
#             'status': request.data.get('status'),
#         }

#         serializer = UserRoleAssignSerializer(data=data)

#         if serializer.is_valid():
#             new_role = serializer.save()
#             # Send email with **plain password**

#             subject = "Your Account Credentials"

#             # Fallback plain text version
#             text_message = f"""
#             Hello {user.name},

#             Your account has been successfully created for accessing the PMO application. Please find your login credentials below:

#             Email: {user.email}
#             Password: {plain_password}

#             Best Regards,
#             ROBOXA TECHNOLOGIES Pvt Ltd.
#             """

#             # HTML version with bold styling
#             html_message = f"""
#             <html>
#             <body>
#                 <p>Hello {user.name},</p>

#                 <p>Your account has been successfully created for accessing the PMO application. Please find your login credentials below:</p>

#                 <p><strong>Email:</strong> {user.email}<br>
#                 <strong>Password:</strong> {plain_password}</p>

#                 <p>Best Regards,<br><strong>ROBOXA TECHNOLOGIES Pvt Ltd.</strong></p>
#             </body>
#             </html>
#             """

#             email = EmailMultiAlternatives(
#                 subject=subject,
#                 body=text_message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[user.email],
#             )
#             email.attach_alternative(html_message, "text/html")
#             email.send()
#             return Response({
#                 "message": "Roles assigned to user successfully!",
#                 "data": UserRoleAssignSerializer(new_role).data
#             }, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#user role assign
@swagger_auto_schema(
    method='post',
    operation_description="Create or update roles for a user.",
    request_body=UserRoleAssignSerializer,
    responses={
        201: openapi.Response("Roles assigned to user successfully!", UserRoleAssignSerializer),
        400: "Bad Request - Validation errors.",
        404: "User not found.",
        409: "Conflict - User already has roles assigned."
    }
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def assign_or_update_user_roles(request):
    user_id = request.data.get('user_id')
    role_names = request.data.get('role_name', [])

    if not user_id or not role_names:
        return Response({"error": "Both user_id and role_name are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user_role = UserRoleAssign.objects.get(user_id=user_id)

        # Update existing role set
        user_role.role_name = list(set(user_role.role_name).union(set(role_names)))
        user_role.save()

        return Response({
            "message": "User roles updated successfully!",
            "data": UserRoleAssignSerializer(user_role).data
        }, status=status.HTTP_200_OK)

    except UserRoleAssign.DoesNotExist:
        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

        #  Auto-generate a new password
        # from your_app.utils import generate_random_password  # Import your password generator
        generated_password = generate_random_password()

        #  Update user password in DB
        user.set_password(generated_password)
        user.change_password_required = True 
        user.save()

        #  Prepare new role assignment data
        data = {
            'user_id': user.user_id,
            'role_name': role_names,
            'name': request.data.get('name'),
            'email': request.data.get('email'),
            'mobile': request.data.get('mobile'),
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'status': request.data.get('status'),
        }

        serializer = UserRoleAssignSerializer(data=data)
        if serializer.is_valid():
            new_role = serializer.save()

            #  Email with new password
            subject = "Your PMO Account Credentials"

            text_message = f"""
Hello {user.name},

Your account has been successfully created. Below are your login credentials:

Email: {user.email}
Password: {generated_password}


Please check the network you are connected to and use the appropriate URL below to access the PMO Application:
If you are connected to the 'Roboxa' network, please use: http://pmo.roboxaservices.com/
If you are connected otherthan 'Roboxa' network (VPN or external network), please use: http://pub-pmo.roboxaservices.com/

Please log in and change your password immediately.


Best Regards,
ROBOXA TECHNOLOGIES Pvt Ltd.
"""

            html_message = f"""
<html>
<body>
    <p>Hello {user.name},</p>
    <p>Your account has been successfully created. Below are your login credentials:</p>
    <p><strong>Email:</strong> {user.email}<br>
    <strong>Password:</strong> {generated_password}</p>
    <strong>For Your Information:</strong></p>
    <p>Please change your password after logging in.</p>
    <p>Please check the network you are connected to and use the appropriate URL below to access the PMO Application:</p>
    <p>If you are connected to the 'Roboxa' network, please use: http://pmo.roboxaservices.com/ </p>
    <p>If you are connected otherthan 'Roboxa' network (VPN or external network), please use: http://pub-pmo.roboxaservices.com/ </p>

    <p>Best Regards,<br><strong>ROBOXA TECHNOLOGIES Pvt Ltd.</strong></p>
</body>
</html>
"""

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            return Response({
                "message": "Roles assigned to user successfully!",
                "data": UserRoleAssignSerializer(new_role).data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#edit assign roles
@swagger_auto_schema(
    method='patch',  # Changed to PATCH
    operation_description="Edit only the role_name field of an existing user_assign_roles entry.",
    request_body=EditUserRoleAssignSerializer,
    responses={
        200: openapi.Response("User role_name updated successfully!", EditUserRoleAssignSerializer),
        404: "Not Found - User not found.",
        400: "Bad Request - Validation errors."
    }
)
@api_view(['PATCH'])  # Changed to PATCH
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_user_assign_roles(request, user_id):
    try:
        user_role = UserRoleAssign.objects.get(user_id=user_id)
    except UserRoleAssign.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EditUserRoleAssignSerializer(user_role, data=request.data, partial=True)  # partial=True allows partial updates
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User role_name updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#get user assign roles
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all users and Roles",
    responses={200: openapi.Response("List of users.", UserRoleAssignListSerializer(many=True))}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_role_assignments(request):
    """
    Retrieve all user role assignments, including profile details and the last login information from LoginHistory.
    """
    profiles = UserRoleAssign.objects.all()
    serializer = UserRoleAssignListSerializer(profiles, many=True)

    response_data = serializer.data

    return Response({'users': response_data}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve user role assignments by user_id",
    responses={
        200: openapi.Response("User role assignment details.", UserRoleAssignListSerializer),
        404: "Not Found - User role assignment not found."
    }
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_user_role_assignment_by_id(request, user_id):
    """
    Retrieve a specific user's role assignment details.
    """
    try:
        user_role = UserRoleAssign.objects.get(user_id=user_id)
    except UserRoleAssign.DoesNotExist:
        return Response({"error": "User role assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserRoleAssignListSerializer(user_role)
    return Response({"user": serializer.data}, status=status.HTTP_200_OK)


# delete user role assign
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a user role assignment by user_id.",
    responses={
        200: "User role assignment deleted successfully.",
        404: "Not Found - User role assignment not found."
    }
)
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def delete_user_role_assignment(request, user_id):
    """
    Delete a user role assignment by user_id.
    """
    try:
        user_role = UserRoleAssign.objects.get(user_id=user_id)  #  Query by user_id
        user_role.delete()
        return Response({"message": "User role assignment deleted successfully."}, status=status.HTTP_200_OK)
    except UserRoleAssign.DoesNotExist:
        return Response({"error": "User role assignment not found."}, status=status.HTTP_404_NOT_FOUND)

#create new role
@swagger_auto_schema(
    method='post',
    operation_description="Create a new role.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'role_name': openapi.Schema(type=openapi.TYPE_STRING)
        },
        required=['role_name']
    ),
    responses={201: "Role created successfully.", 400: "Role already exists."}
)
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def create_role(request):
    """
    Create a new role in the system.
    """
    role_name = request.data.get('role_name')

    if not role_name:
        return Response({'message': 'Role name is required'}, status=status.HTTP_400_BAD_REQUEST)

    role, created = Roles.objects.get_or_create(role_name=role_name)

    if created:
        return Response({'message': 'Role created successfully!', 'role': role_name}, status=status.HTTP_201_CREATED)
    else:
        return Response({'message': 'Role already exists!'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_description="Edit an existing role.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'role_name': openapi.Schema(type=openapi.TYPE_STRING, description="Updated role name")
        },
        required=['role_name']
    ),
    responses={
        200: "Role updated successfully.",
        400: "Invalid request.",
        404: "Role not found."
    }
)
@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def edit_role(request, role_id):
    """
    Edit an existing role by ID.
    """
    new_role_name = request.data.get('role_name')

    if not new_role_name:
        return Response({'message': 'Role name is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        role = Roles.objects.get(id=role_id)
        
        # Check if the new role name already exists (except the current role)
        if Roles.objects.exclude(id=role_id).filter(role_name=new_role_name).exists():
            return Response({'message': 'Role name already in use!'}, status=status.HTTP_400_BAD_REQUEST)

        role.role_name = new_role_name
        role.save()

        return Response({'message': 'Role updated successfully!', 'role': new_role_name}, status=status.HTTP_200_OK)

    except Roles.DoesNotExist:
        return Response({'message': 'Role not found!'}, status=status.HTTP_404_NOT_FOUND)

# Get All Roles API
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all roles.",
    responses={200: openapi.Response("List of roles.", RolesSerializer(many=True))}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_roles(request):
    """
    Retrieve all roles available in the system.
    """
    roles = Roles.objects.all()
    serializer = RolesSerializer(roles, many=True)
    return Response({'roles': serializer.data}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a role by its ID.",
    responses={
        200: openapi.Response("Role details.", RolesSerializer()),
        404: "Role not found."
    }
)

#get role by id
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_role_by_id(request, role_id):
    """
    Retrieve a role by its ID.
    """
    try:
        role = Roles.objects.get(id=role_id)
        serializer = RolesSerializer(role)
        return Response({'role': serializer.data}, status=status.HTTP_200_OK)
    except Roles.DoesNotExist:
        return Response({'message': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)

