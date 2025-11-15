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

AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME")
INSTALLED_APPS.append("storages")

STORAGES = {
    "default": {
        "BACKEND": "mysite.storage.PublicMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "mysite.storage.StaticStorage",
    },
}

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

AWS_ACL = None
AWS_STATIC_STORAGE_BUCKET_NAME = config("AWS_STATIC_STORAGE_BUCKET_NAME")
AWS_MEDIA_STORAGE_BUCKET_NAME = config("AWS_MEDIA_STORAGE_BUCKET_NAME")
STATIC_URL = f'https://{AWS_STATIC_STORAGE_BUCKET_NAME}.s3.amazonaws.com/static/'
MEDIA_URL = f'https://{AWS_MEDIA_STORAGE_BUCKET_NAME}.s3.amazonaws.com/media/'

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


# reCAPTCHA Configuration
# Get keys from https://www.google.com/recaptcha/admin
RECAPTCHA_PUBLIC_KEY = config('CAPTCHA_V2_SITE_KEY')
RECAPTCHA_PRIVATE_KEY = config('CAPTCHA_V2_SECRET_KEY')

# EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config("EMAIL_HOST", cast=str, default=None)
EMAIL_PORT = config("EMAIL_PORT", cast=str, default='587') # Recommended
EMAIL_HOST_USER = config("EMAIL_HOST_USER", cast=str, default=None)
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", cast=str, default=None)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=True)  # Use EMAIL_PORT 587 for TLS
EMAIL_USE_SSL = config("EMAIL_USE_SSL", cast=bool, default=False)  # EUse MAIL_PORT 465 for SSL
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')


# Django admins and managers
ADMIN_USER_NAME=config("ADMIN_USER_NAME", default="Admin user")
ADMIN_USER_EMAIL=config("ADMIN_USER_EMAIL", default=None)

MANAGERS=[]
ADMINS=[]
if all([ADMIN_USER_NAME, ADMIN_USER_EMAIL]):
    ADMINS +=[
        (f'{ADMIN_USER_NAME}', f'{ADMIN_USER_EMAIL}')
    ]
    MANAGERS=ADMINS