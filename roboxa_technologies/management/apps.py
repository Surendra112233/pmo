# management/apps.py
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = 'management'  # Make sure 'management' matches the actual app folder name

    def ready(self):
        import management.signals  # Ensure the signals are loaded when the app is ready
