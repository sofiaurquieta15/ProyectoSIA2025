"""
WSGI config for ProyectoKine project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# *** LÍNEA PARA RUTA ABSOLUTA EN DOCKER ***
sys.path.append('/app')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ProyectoKine.settings.deploy")

application = get_wsgi_application()