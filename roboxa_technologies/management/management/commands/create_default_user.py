from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from user_management.models import UserProfile, Roles, UserRoleAssign

class Command(BaseCommand):
    help = "Create a default admin user with the 'User Admin' role"

    def handle(self, *args, **kwargs):
        admin_user_id = "RBX00"
        default_email = "roboxa@gmail.com"
        default_password = "Roboxa@123"
        default_mobile = "9999999998"
        default_start_date = "2025-03-03"
        default_end_date = "2029-07-30"

        # Hash password before saving
        hashed_password = make_password(default_password)

        # Step 1: Create or get the user in UserProfile
        user, created = UserProfile.objects.get_or_create(
            user_id=admin_user_id,
            defaults={
                "name": "Roboxa",
                "password": hashed_password,  # Store as hashed password
                "email": default_email,
                "mobile": default_mobile,
                "start_date": default_start_date,
                "end_date": default_end_date,
                "status": "active"
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Successfully created user {admin_user_id}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"User {admin_user_id} already exists"))

        # Step 2: Ensure "User Admin" role exists
        user_admin_role, _ = Roles.objects.get_or_create(role_name="User Admin")

        # Step 3: Assign role to UserRoleAssign
        role_assign, role_created = UserRoleAssign.objects.get_or_create(
            user_id=user,
            defaults={
                "name": user.name,
                "email": user.email,
                "mobile": user.mobile,
                "start_date": user.start_date,
                "end_date": user.end_date,
                "status": user.status,
                "role_name": ["User Admin"]  # Store as JSON array
            }
        )

        if role_created:
            self.stdout.write(self.style.SUCCESS(f"Role 'User Admin' assigned to {admin_user_id}"))
        else:
            # Update roles if needed
            if "User Admin" not in role_assign.role_name:
                role_assign.role_name.append("User Admin")
                role_assign.save()
                self.stdout.write(self.style.SUCCESS(f"Updated roles for {admin_user_id}"))

        self.stdout.write(self.style.SUCCESS("Default user setup complete!"))
