from django.apps import AppConfig

class First_appConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'First_app'
    
    def ready(self):
        import First_app.signals