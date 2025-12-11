from .base import *
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "db_proyectokine",
        "USER": "user_proyectokine",
        "PASSWORD": "123456",
        "HOST": "localhost",
        "PORT": "5432"
    }
}

