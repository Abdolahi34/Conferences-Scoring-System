from django.apps import AppConfig


class ScoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'score'
    verbose_name = 'امتیاز'

    def ready(self):
        import score.signals
