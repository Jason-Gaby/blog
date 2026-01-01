from django.apps import AppConfig
from django.conf import settings
import os

class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        # 1. Import your package
        import blog_content

        # 2. Define where the .env for blog_content is
        dotenv_path = os.path.join(settings.PROJECT_ROOT, settings.ENV_DIR, ".env.blog_content")

        # 3. Inject Wagtail's environment into the package
        # This "re-initializes" the settings object, overriding the
        # default local .env that might have been loaded.
        blog_content.settings.initialize(
            env_file_path=dotenv_path
        )