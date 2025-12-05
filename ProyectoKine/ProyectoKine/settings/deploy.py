# ProyectoKine/ProyectoKine/settings/deploy.py
import os
from .base import * # Importa todas las configuraciones base

# --- 1. Seguridad ---
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# --- 2. Configuración de Base de Datos (Postgres en Docker) ---
if os.environ.get('POSTGRES_HOST') is not None:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# --- 3. Rutas de Archivos (Necesarias para Docker Volumes) ---
STATIC_ROOT = os.environ.get('STATIC_ROOT', '/vol/staticfiles')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/vol/media')