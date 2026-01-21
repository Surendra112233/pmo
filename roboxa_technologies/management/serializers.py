from rest_framework import serializers
from django.contrib.auth.models import User
import re

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    otp = serializers.IntegerField(required=False)

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    confirm_password = serializers.CharField(write_only=True)

    def validate_confirm_password(self, value):
        """Ensure password meets security criteria."""
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