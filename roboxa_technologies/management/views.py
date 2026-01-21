
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
import random
from django.utils.timezone import now
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .models import OTP,LoginHistory,ForgotPasswordRequest
from user_management.models import UserRoleAssign,UserProfile
# from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from management.serializers import ForgotPasswordSerializer
from employee.models import Employee
from django.core.mail import EmailMultiAlternatives
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BasicAuthentication
from django.contrib.auth.hashers import check_password,make_password
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken, TokenError



# User = get_user_model()


# login view
class LoginView(APIView):
    authentication_classes = []         # Disable token/session authentication
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="User Login with Email, Password, and OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password", "otp"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="User's email address"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="User's password"),
                "otp": openapi.Schema(type=openapi.TYPE_INTEGER, description="One-Time Password (OTP) received via email"),
            },
        ),
        responses={
            200: "Login successful!",
            401: "Invalid email, password, or OTP",
            400: "Invalid request data"
        }
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        otp = request.data.get('otp')

        # Step 1: Validate if email and password are provided
        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # # Step 2: Fetch User
        # user = UserProfile.objects.filter(email=email).first()

        # # Step 3: Check if user exists and password matches
        # if not user or user.password != password:
        #     return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
        # Step 2: Fetch User
        user = UserProfile.objects.filter(email=email).first()

        # Step 3: Check for both incorrect email & incorrect password
        if not user:
            if not UserProfile.objects.filter(password=password).exists():
                return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)
            return Response({"error": "Incorrect email ID"}, status=status.HTTP_401_UNAUTHORIZED)

        # Step 4: Check for incorrect password
        # if user and user.password != password:
        #     return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not check_password(password, user.password):
            return Response({"error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

         # Step 5: Check if user's `end_date` is expired
        if user.end_date and user.end_date < now().date():
            return Response({"error": "Your account has expired and you cannot log in."}, status=status.HTTP_403_FORBIDDEN)
        
        # Step 6: Fetch user roles (Ensure user is not None)
        roles = UserRoleAssign.objects.filter(user_id_id=user.user_id).values_list('role_name', flat=True)
        if not roles:
            return Response({"error": "User has no assigned roles, cannot log in"}, status=status.HTTP_401_UNAUTHORIZED)

        # Step 7: Check if the user's status is 'active'
        if user.status.strip().lower() != "active":  
            return Response({"error": "User is inactive, cannot log in"}, status=status.HTTP_401_UNAUTHORIZED)

        #for testing from here
        # if str(otp) == "123456": 
        #     pass  
        # else:
        #     otp_entry = OTP.objects.filter(user=user, otp=str(otp), expires_on__gte=timezone.now()).first()
        #     if not otp_entry:
        #         return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_401_UNAUTHORIZED)
        # #for testing till here

        #for production from here
        otp_entry = OTP.objects.filter(user=user, otp=str(otp), expires_on__gte=timezone.now()).first()
        if not otp_entry:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_401_UNAUTHORIZED)
        #for production till here

        # Step 9 Fetch Employee designation
        employee = Employee.objects.filter(employee_code=user.user_id).first()
        designation = employee.designation if employee else "N/A"
        
         # Store login attempt in LoginHistory
        LoginHistory.objects.create(user_id=user.user_id, username_or_email=user.email, created_on=now())
        
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        
        # Generate JWT Token
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful!",
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user_name": user.name,
            "roles": list(roles),
            "designation": designation 
        }, status=status.HTTP_200_OK)


# sendotp view
class SendOTPView(APIView):
    authentication_classes = []  # No authentication
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_summary="Send OTP to user's email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="User's email address")},
        ),
        responses={200: "OTP sent successfully", 400: "Invalid request data", 404: "User not found"},
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # FIXED: Query UserProfile instead of User
        user = UserProfile.objects.filter(email=email).first()
        
        if user:
            otp = random.randint(100000, 999999)
            otp_generated_at = timezone.now()
            expires_on = otp_generated_at + timedelta(minutes=1)

            # Save OTP details
            OTP.objects.create(
                user=user,  # Ensure OTP is linked to UserProfile
                otp=str(otp),
                generated_on=otp_generated_at,
                expires_on=expires_on
            )

        #     send_mail(
        #     'Your OTP Code',
        #     f'Hi {user.name},\n\nYour OTP to login ROBOXA PMO Application is : {otp}',
        #     settings.DEFAULT_FROM_EMAIL,
        #     [email],
        #     fail_silently=False,
        # )
            subject = 'OTP to Login '
            from_email = settings.DEFAULT_FROM_EMAIL
            to = [email]

            text_content = f'Hi {user.name},\n\nYour OTP to login ROBOXA PMO Application is: {otp}\n\nThanks & Regards,\nROBOXA PMO'
            html_content = f'''
            <p>Hi {user.name},</p>
            <p>Your OTP to login ROBOXA PMO Application is: <strong>{otp}</strong></p>
            <p style="margin-top: 30px;">Thanks & Regards,<br><strong>ROBOXA PMO.</strong></p>
            '''

            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()      

            return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Please maintain correct email ID."}, status=status.HTTP_404_NOT_FOUND)
        

# class ForgotPasswordView(APIView):
#     authentication_classes = []         # Disable token/session authentication
#     permission_classes = [AllowAny]
#     @swagger_auto_schema(
#         operation_summary="Reset password after OTP verification",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=['email', 'confirm_password'],
#             properties={
#                 'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="User's email address"),
#                 # 'otp': openapi.Schema(type=openapi.TYPE_INTEGER, description="OTP sent to user's email"),
#                 # 'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="New password"),
#                 'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="Confirm password"),
#             },
#         ),
#         responses={200: "Password reset successfully", 400: "Invalid OTP or OTP expired", 404: "User not found"},
#     )
#     def post(self, request):
#         # Validate request data using serializer
#         serializer = ForgotPasswordSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         # Extract validated data
#         email = serializer.validated_data['email']
#         # otp = serializer.validated_data['otp']
#         confirm_password = serializer.validated_data['confirm_password']

#         # Fetch the user
#         user = UserProfile.objects.filter(email=email).first()
#         if not user:
#             return Response({"error": "Incorrect email ID"}, status=status.HTTP_404_NOT_FOUND)

#         # Fetch OTP object
#         # otp_obj = OTP.objects.filter(user=user, otp=otp).first()
#         # if not otp_obj:
#         #     return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if OTP is expired
#         # otp_age = timezone.now() - otp_obj.generated_on
#         # if otp_age > timedelta(minutes=1):
#         #     return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if new password is the same as the old password
#         if user.password == confirm_password:
#             return Response({"error": "New password cannot be the same as the old password"}, status=status.HTTP_400_BAD_REQUEST)


#         # Hash and save new password
#         user.password = confirm_password 
#         user.save(update_fields=["password"])

#         # Delete OTP after successful reset
#         # otp_obj.delete()

#         return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Reset password after OTP verification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'confirm_password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: "Password reset successfully", 400: "Invalid data", 404: "User not found"},
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        confirm_password = serializer.validated_data['confirm_password']

        user = UserProfile.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Incorrect email ID"}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Check if new password is same as old
        if check_password(confirm_password, user.password):
            return Response({"error": "New password cannot be the same as the old password"}, status=status.HTTP_400_BAD_REQUEST)

        #  Update the actual user password
        user.password = make_password(confirm_password)
        user.save(update_fields=["password"])  # <- THIS is what was missing

        # Optionally store in ForgotPasswordRequest for tracking
        ForgotPasswordRequest.objects.update_or_create(
            email=email,
            defaults={
                "new_password": user.password,
                "confirm_password": user.password,
                "created_on": timezone.now()
            }
        )

        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)



# token access
# token access
# class CustomTokenObtainPairSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')

#         # try:
#         #     user = UserProfile.objects.get(email=email)
#         # except UserProfile.DoesNotExist:
#         #     raise serializers.ValidationError('Incorrect Email ID.')

#         # if user.password != password:  # Direct comparison (plain text)
#         #     raise serializers.ValidationError('Incorrect password.')
#         # Step 1: Check if both email & password are incorrect
#         user = UserProfile.objects.filter(email=email).first()
#         if not user:
#             if not UserProfile.objects.filter(password=password).exists():
#                 raise serializers.ValidationError({"error": "Incorrect password"})
#             raise serializers.ValidationError({"error": "Incorrect email ID"})

#         # Step 2: Check if password is incorrect
#         if user.password != password:  # Direct comparison (not secure, ideally hash passwords)
#             raise serializers.ValidationError({"error": "Incorrect password"})
        

#         if user.status.strip().lower() != "active":
#             raise serializers.ValidationError('User is inactive, cannot log in.')
        
#         # Fetch user roles
#         roles = UserRoleAssign.objects.filter(user_id=user.user_id).values_list('role_name', flat=True)

#         if not roles:  # If user has no assigned roles
#             raise serializers.ValidationError('User has no assigned roles,cannot log in.')

#         refresh = RefreshToken.for_user(user)
#         return {
#             'message': 'User is Valid',
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#             'user': {
#                 'id': user.user_id,
#                 'email': user.email,
#                 'name': user.name,
#                 'change_password_required': user.change_password_required  

#             }
#         }

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = UserProfile.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"error": "Incorrect email ID"})

        #  Correct password check
        if not user.check_password(password):
            raise serializers.ValidationError({"error": "Incorrect password"})

        #  Active check
        if user.status.strip().lower() != "active":
            raise serializers.ValidationError({"error": "User is inactive"})

        #  Role check
        roles = UserRoleAssign.objects.filter(user_id=user.user_id).values_list('role_name', flat=True)
        if not roles:
            raise serializers.ValidationError({"error": "User has no assigned roles"})

        refresh = RefreshToken.for_user(user)

        return {
            'message': 'Login successful!',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.user_id,
                'email': user.email,
                'name': user.name,
                'change_password_required': user.change_password_required
            },
            'roles': list(roles),
        }

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@swagger_auto_schema(
    method='post',
    operation_summary="Reset Password by Email",
    operation_description="Allows password change using email (e.g., for forgot password or admin reset).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["email", "new_password"],
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="User's registered email"),
            "new_password": openapi.Schema(type=openapi.TYPE_STRING, description="New password to be set"),
        },
    ),
    responses={
        200: openapi.Response(description="Password updated successfully."),
        400: openapi.Response(description="Missing fields or invalid email."),
        404: openapi.Response(description="User not found."),
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([]) 
def change_password(request):
    email = request.data.get("email")
    new_password = request.data.get("new_password")

    if not email or not new_password:
        return Response({"error": "Email and new password are required."}, status=400)

    try:
        user = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return Response({"error": "User not found."}, status=404)

    user.set_password(new_password)
    user.change_password_required = False
    user.save()

    return Response({"message": "Password updated successfully."}, status=200)

#refresh token
@swagger_auto_schema(
    method='post',
    operation_summary="Refresh Login using Email and Refresh Token",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["email", "refresh_token"],
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
            "refresh_token": openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={
        200: "New access and refresh token generated.",
        400: "Invalid token or email.",
        401: "Unauthorized"
    }
)
@api_view(['POST'])
@authentication_classes([])  # No auth required
@permission_classes([AllowAny])
def login_refresh_token(request):
    email = request.data.get("email")
    refresh_token = request.data.get("refresh_token")

    if not email or not refresh_token:
        return Response({"error": "Email and refresh_token are required."}, status=400)

    try:
        user = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return Response({"error": "Invalid email."}, status=400)

    try:
        # Validate and decode refresh token
        token = RefreshToken(refresh_token)
        if str(token.payload.get("user_id")) != user.user_id:
            return Response({"error": "Token does not match user."}, status=401)

        # Generate new tokens
        new_refresh = RefreshToken.for_user(user)

        # Get roles
        roles = UserRoleAssign.objects.filter(user_id=user.user_id).values_list('role_name', flat=True)

        # Get designation
        employee = Employee.objects.filter(employee_code=user.user_id).first()
        designation = employee.designation if employee else "N/A"

        return Response({
            "message": "Login successful!",
            "access_token": str(new_refresh.access_token),
            "refresh_token": str(new_refresh),
            "user_name": user.name,
            "roles": list(roles),
            "designation": designation
        }, status=200)

    except TokenError as e:
        return Response({"error": "Invalid or expired refresh token."}, status=400)

#verify otp 
class VerifyOTPView(APIView):
    authentication_classes = []  # No authentication
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify OTP for a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="User's email address"),
                'otp': openapi.Schema(type=openapi.TYPE_INTEGER, description="One-Time Password received by email"),
            },
        ),
        responses={
            200: "OTP is valid.",
            400: "Invalid request data.",
            404: "User not found.",
            401: "Invalid or expired OTP."
        }
    )
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        # Validate input
        if not email or not otp:
            return Response({"error": "Both email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user
        user = UserProfile.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # For testing purposes, allow fixed OTP (comment in production)
        # if str(otp) == "123456":
        #     return Response({"message": "OTP verified (test OTP accepted)."}, status=status.HTTP_200_OK)

        # # Validate OTP
        otp_entry = OTP.objects.filter(user=user, otp=str(otp), expires_on__gte=timezone.now()).first()
        if otp_entry:
            return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_401_UNAUTHORIZED)