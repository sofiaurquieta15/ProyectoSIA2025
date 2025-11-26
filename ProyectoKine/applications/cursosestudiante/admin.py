from django.contrib import admin
from .models import *

# Register your models here.

class AvanceAdmin(admin.ModelAdmin):
    list_display = ('id_estudiante','id_curso','porcentajeavance','completado')
    list_filter = ('completado','id_curso__nombrecurso')
    search_fields = ('id_estudiante__nombre',)
    list_select_related = ('id_estudiante','id_curso')

admin.site.register(Avance,AvanceAdmin)

