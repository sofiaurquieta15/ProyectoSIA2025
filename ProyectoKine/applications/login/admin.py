from django.contrib import admin
from .models import *
# Register your models here.

class DocenteAdmin(admin.ModelAdmin):
    list_display = ('nombre_docente', 'correo_docente')
    search_fields = ('nombre_docente',)

class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo_institucional')
    search_fields = ('nombre',)

admin.site.register(Docente, DocenteAdmin)
admin.site.register(Estudiante, EstudianteAdmin)