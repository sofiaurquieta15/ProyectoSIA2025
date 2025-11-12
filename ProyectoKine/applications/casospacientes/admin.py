from django.contrib import admin
from .models import *

admin.site.register(Paciente)
admin.site.register(Etapa)
admin.site.register(TipoPregunta)
admin.site.register(Pregunta)
admin.site.register(Respuesta)