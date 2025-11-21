from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        # 🟢 Import the signals file to connect the handlers
        import core.signals