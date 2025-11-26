from django.contrib import admin
from .models import *

class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombrecurso','id_docente','fechacreacion')
    list_filter = ('nombrecurso','id_docente__nombre_docente')
    search_fields = ('nombrecurso',)
    list_select_related = ('id_docente',)


admin.site.register(Curso,CursoAdmin)
