from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-v%12k_2hq!um5)_$#pdy473gyu0*5v*g3s%d0etqcg(e5)%t80"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
