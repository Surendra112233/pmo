from rest_framework import serializers
from .models import UserProfile, UserRoleAssign,Roles
from management.models import LoginHistory
import re
from django.utils.timezone import localtime
import pytz
 

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'name', 'password', 'email', 'mobile',
            'start_date', 'end_date', 'status',
            'created_at', 'updated_at'
        ]

    def validate_user_id(self, value):
        if not value.startswith('RBX'):
            raise serializers.ValidationError("The user_id must start with the prefix 'RBX'.")
        if not value[3:].isdigit():
            raise serializers.ValidationError("The user_id must have numeric characters after 'RBX'.")
        return value

    def validate_name(self, value):
        if not re.fullmatch(r'^[A-Za-z ]+$', value.strip()):
            raise serializers.ValidationError("The name must contain only alphabetic characters and spaces.")
        return value

    def validate_password(self, value):
        # Only validate if provided
        if not value:
            return value

        if value.isdigit():
            raise serializers.ValidationError("Password cannot contain only numbers.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def validate_mobile(self, value):
        if not re.fullmatch(r'[+\-\d\s]+', value):
            raise serializers.ValidationError("Mobile number can only contain digits, '+', '-', or spaces.")
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10:
            raise serializers.ValidationError("Mobile number must contain at least 10 digits.")
        return value

    def validate_email(self, value):
        if not value.endswith('@roboxaservices.com'):
            raise serializers.ValidationError("Email must belong to the 'roboxaservices.com' domain.")
        return value

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be greater than start date."})
        return data

class UserListSerializer(serializers.ModelSerializer):
    last_login = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)  # Only password should be write-only
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'name', 'email', 'password', 'mobile', 'start_date', 'end_date', 'status', 'last_login', 'created_at', 'updated_at']

    def get_last_login(self, obj):
        last_login = LoginHistory.objects.filter(username_or_email=obj.email).order_by('-created_on').first()
        if last_login:
            # Convert UTC to IST
            ist = pytz.timezone("Asia/Kolkata")
            return localtime(last_login.created_on, ist).isoformat()
        return None
    


class UserEditSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Optional in edit

    class Meta:
        model = UserProfile
        fields = [
            'user_id', 'name', 'email', 'mobile',
            'start_date', 'end_date', 'status', 'password'
        ]

    def validate_user_id(self, value):
        if not value.startswith('RBX'):
            raise serializers.ValidationError("The user_id must start with the prefix 'RBX'.")
        if not value[3:].isdigit():
            raise serializers.ValidationError("The user_id must have numeric characters after 'RBX'.")
        return value

    def validate_name(self, value):
        if not re.fullmatch(r'^[A-Za-z ]+$', value.strip()):
            raise serializers.ValidationError("The name must contain only alphabetic characters and spaces.")
        return value

    def validate_mobile(self, value):
        if not re.fullmatch(r'[+\-\d\s]+', value):
            raise serializers.ValidationError("Mobile number can only contain digits, '+', '-', or spaces.")
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) < 10:
            raise serializers.ValidationError("Mobile number must contain at least 10 digits.")
        return value

    def validate_email(self, value):
        if not value.endswith('@roboxaservices.com'):
            raise serializers.ValidationError("Email must belong to the 'roboxaservices.com' domain.")
        return value

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be greater than start date."})
        return data

    def update(self, instance, validated_data):
        # Update instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class UserRoleAssignSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(write_only=True)  # Accept user_id as input

    class Meta:
        model = UserRoleAssign
        fields = ['user_id', 'name', 'email', 'mobile', 'start_date', 'end_date', 'status', 'role_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')  # Extract user_id from validated data
        try:
            user = UserProfile.objects.get(user_id=user_id)  # Fetch the UserProfile instance
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User does not exist.'})

        validated_data['user_id'] = user  # Assign the UserProfile instance
        return UserRoleAssign.objects.create(**validated_data)

    def to_representation(self, instance):
        """
        Ensure role_name is always returned as a flat list.
        """
        data = super().to_representation(instance)
        if isinstance(data['role_name'], list) and len(data['role_name']) == 1 and isinstance(data['role_name'][0], list):
            data['role_name'] = data['role_name'][0]  # Flatten the nested list
        return data

    
class EditUserRoleAssignSerializer(serializers.ModelSerializer):
    role_name = serializers.ListField(
        child=serializers.CharField(),  # Ensures role_name is a list of strings
        required=True
    )

    class Meta:
        model = UserRoleAssign
        fields = ['role_name']


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['id', 'role_name']

class UserRoleAssignListSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user_id.user_id", read_only=True)
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = UserRoleAssign
        fields = [
            'id', 'user_id', 'name', 'email', 'mobile',
            'start_date', 'end_date', 'status', 'role_name',
            'last_login', 'created_at', 'updated_at'
        ]

    def get_last_login(self, obj):
        last_login = LoginHistory.objects.filter(
            username_or_email=obj.email
        ).order_by('-created_on').first()

        if last_login:
            ist = pytz.timezone("Asia/Kolkata")
            return localtime(last_login.created_on, ist).isoformat()
        return None

