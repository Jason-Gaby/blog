from decouple import Config, RepositoryEnv
import os

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
MEDIA_URL = f'https://{config("AWS_MEDIA_STORAGE_BUCKET_NAME")}.s3.{config("AWS_S3_REGION_NAME")}.amazonaws.com/media/'

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),  # Adjust level for production (e.g., INFO, WARNING, ERROR)
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
                    "level": "DEBUG",  # You can keep DEBUG for detailed file logs
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "/home/ec2-user/logs/debug.log",  # Specify production log file path
                    "maxBytes": 1024 * 1024 * 5,  # 5 MB
                    "backupCount": 5,  # Keep 5 backup files
                    "formatter": "verbose",
                },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "propagate": True,
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