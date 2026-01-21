from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError
from django.db import transaction

class User_ManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_management'

    def ready(self):
        from .models import Roles

        default_roles = [
            "DataAdmin",
            "UserAdmin",
            "PMO",
            "Employee",
            "Manager",
            "HR",
            "DeliveryHead",
            "Management",
            "ITAdmin",
            "Allocation",
            "RegionalHead",
            "TSAdmin",
            "DHAdmin",
            "SBUHead"
        ]

        try:
            with transaction.atomic():
                # Add missing roles
                for role_name in default_roles:
                    Roles.objects.get_or_create(role_name=role_name)

                # Remove roles not in the list
                Roles.objects.exclude(role_name__in=default_roles).delete()

        except (OperationalError, ProgrammingError):
            # Ignore errors during migration or initial DB setup
            pass
