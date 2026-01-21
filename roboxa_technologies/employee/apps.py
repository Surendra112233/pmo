from django.apps import AppConfig

class EmployeeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employee'

    def ready(self):
        from employee.management.commands import scheduler
        scheduler.start()
