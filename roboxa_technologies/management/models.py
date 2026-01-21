from django.db import models
from django.utils import timezone
from user_management.models import UserProfile  # Link to UserProfile

class LoginHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to UserProfile
    username_or_email = models.CharField(max_length=100)  # Email/Username used for login
    password = models.CharField(max_length=128)  # Store hashed password
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of login

    def __str__(self):
        return f"Login attempt for {self.user.name} at {self.created_on}"

    class Meta:
        ordering = ['-created_on']  # Sort by most recent login first


class ForgotPasswordRequest(models.Model):
    email = models.EmailField()  # Email of the user requesting the reset
    new_password = models.CharField(max_length=255)  # The new password entered by the user
    confirm_password = models.CharField(max_length=255)  # Confirm password field
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp when the request is created

    def __str__(self):
        return f"Forgot password request for {self.email}"

    def passwords_match(self):
        """Validate if the new password and confirm password match."""
        return self.new_password == self.confirm_password
    
class OTP(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to the User model
    otp = models.IntegerField()  # OTP (typically a 6-digit code)
    generated_on = models.DateTimeField(default=timezone.now)  # Timestamp of when the OTP was generated
    expires_on = models.DateTimeField()  # Timestamp of when the OTP expires (e.g., after 10 minutes)

    def __str__(self):
        return f"OTP for {self.user.username}"

    def is_valid(self):
        """Check if the OTP is still valid."""
        return timezone.now() <= self.expires_on