from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from user_management.models import UserProfile  # adjust if needed

class Command(BaseCommand):
    help = 'Encrypts all plain-text passwords for existing users'

    def handle(self, *args, **kwargs):
        updated_count = 0

        for user in UserProfile.objects.all():
            if user.password and not user.password.startswith('pbkdf2_'):
                self.stdout.write(f"Encrypting password for: {user.email}")
                user.password = make_password(user.password)
                user.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f" Done. Updated {updated_count} user(s)."))
