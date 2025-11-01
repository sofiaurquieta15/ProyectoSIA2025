from django.contrib import admin
from .models import *

admin.site.register(Paciente)
admin.site.register(Diagnostico)
admin.site.register(Respuesta)