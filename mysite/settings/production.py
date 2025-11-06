from decouple import Config, RepositoryEnv

from .base import *

config = Config(RepositoryEnv(".env.production"))

DEBUG = False

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", "").split(",")
CSRF_TRUSTED_ORIGINS = config("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
INSTALLED_APPS.append("storages")
STORAGES["staticfiles"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"
STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"
STATIC_URL = f'https://{config("AWS_STATIC_STORAGE_BUCKET_NAME")}.s3.{config("AWS_S3_REGION_NAME")}.amazonaws.com/static/'
MEDIA_URL = f'https://{config("AWS_MEDIA_STORAGE_BUCKET_NAME")}.s3.{config("AWS_S3_REGION_NAME")}.amazonaws.com/static/'

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    },
}

WAGTAIL_REDIRECTS_FILE_STORAGE = "cache"


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': config('DB_HOST'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'PORT': config('DB_PORT'),
    }
}

try:
    from .local import *
except ImportError:
    pass