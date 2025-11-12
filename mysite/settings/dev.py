from .base import *
from decouple import Config, RepositoryEnv

config = Config(RepositoryEnv(".env.dev"))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Default storage settings
# See https://docs.djangoproject.com/en/5.2/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder", #This code searchs in all ./*/static/* files, omit for now.
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-v%12k_2hq!um5)_$#pdy473gyu0*5v*g3s%d0etqcg(e5)%t80"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# reCAPTCHA Configuration
# Get keys from https://www.google.com/recaptcha/admin
RECAPTCHA_PUBLIC_KEY = config('CAPTCHA_V2_SITE_KEY')
RECAPTCHA_PRIVATE_KEY = config('CAPTCHA_V2_SECRET_KEY')


try:
    from .local import *
except ImportError:
    pass
