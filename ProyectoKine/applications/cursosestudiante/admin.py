from django.contrib import admin
from .models import *

# Register your models here.

class AvanceAdmin(admin.ModelAdmin):
    list_display = ('id_estudiante','id_curso','porcentajeavance','completado')
    list_filter = ('completado','id_curso__nombrecurso')
    search_fields = ('id_estudiante__nombre',)
    list_select_related = ('id_estudiante','id_curso')

class SolicitudRevisionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'paciente', 'etapa_solicitud', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'etapa_solicitud', 'curso')
    search_fields = ('estudiante__nombre', 'paciente__nombre')

admin.site.register(Avance,AvanceAdmin)
admin.site.register(Enrolamiento)
admin.site.register(SolicitudRevision, SolicitudRevisionAdmin)

