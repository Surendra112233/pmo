from django.apps import AppConfig

class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'  # This must match the package path
    label = 'inventory'
