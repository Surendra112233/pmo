from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

from datetime import date

class UserProfileManager(BaseUserManager):
    def create_user(self, user_id, email, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        
        now = timezone.now().date()  # Or timezone.now() depending on your model field type

        user = self.model(
            user_id=user_id,
            email=self.normalize_email(email),
            name=name,
            start_date=now,
            end_date=now,          #  Set end_date to now or a future date if needed
            status='active',
            is_active=True,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, email, name, password=None, **extra_fields):
        user = self.create_user(
            user_id=user_id,
            email=email,
            name=name,
            password=password,
            **extra_fields
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class UserProfile(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    change_password_required = models.BooleanField(default=True)

    # Required by Django auth system
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)

    # Admin-related fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Optional metadata fields
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, default="active")
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_id', 'name']

    def __str__(self):
        return self.user_id
    
class Roles(models.Model): 
    id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.role_name

class UserRoleAssign(models.Model):
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, to_field='user_id')
    name = models.CharField(max_length=80, null=False, blank=False)    
    email = models.CharField(max_length=100, null=False, blank=False)  
    mobile = models.CharField(max_length=15, null=False, blank=False)  
    start_date = models.DateField(null=True, blank=True)           
    end_date = models.DateField(null=True, blank=True)             
    status = models.CharField(max_length=10)
    role_name = models.JSONField(default=list) 
    created_at = models.DateTimeField(default=now, editable=False)  # Auto-set at creation
    updated_at = models.DateTimeField(auto_now=True)  # Auto-update on save

    def __str__(self):
        return f"{self.name} - {self.role_name}"
    