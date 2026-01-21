# pmo/apps.py
from django.apps import AppConfig
import os
from decouple import config  

class PmoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pmo'

    def ready(self):
        """
        Auto-apply all model changes (add, delete, modify fields) across all apps
        when runserver is executed (works in dev/prod).
        """
        # Prevent duplicate migration run on auto-reloader
        if os.environ.get('RUN_MAIN') == 'true':
            from django.core.management import call_command

            # Optional: use .env flag to control auto-migration
            auto_migrate = config('AUTO_MIGRATE', default=True, cast=bool)
            if not auto_migrate:
                return

            try:
                print(" Auto-making and applying migrations for all apps...")
                call_command("makemigrations", interactive=False)
                call_command("migrate", interactive=False)
                print(" Migrations complete.")
            except Exception as e:
                print(f" Migration Error: {e}")
