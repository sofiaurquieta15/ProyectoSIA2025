from django.contrib import admin
from .models import *

class TipoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ['nombre',]

class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre','edad','sexo','tipo_caso','id_curso')
    list_filter = ('tipo_caso__nombre', 'id_curso__nombrecurso') 
    search_fields = ('id_curso__nombrecurso',) 
    list_select_related = ('tipo_caso','id_curso')

class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombreetapa', 'numetapa', 'id_paciente', 'urlvideo','tipo_pregunta')
    list_filter = ('id_paciente','tipo_pregunta')
    search_fields = ('nombreetapa',) 
    list_select_related = ('id_paciente',)

class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('titulo','docente','id_etapa','tipo')
    list_filter = ('tipo','docente__nombre_docente')
    search_fields = ('docente__nombre_docente',)
    list_select_related = ('docente','id_etapa')

class OpcionMultipleAdmin(admin.ModelAdmin):
    list_display = ('pregunta','texto_opcion','is_correct')
    list_filter = ('is_correct',)
    search_fields = ('pregunta__titulo',)
    list_select_related = ('pregunta',)

class RegistroAdmin(admin.ModelAdmin):
    list_display = ('id_pregunta', 'id_estudiante','fecha_envio')
    list_filter = ('id_pregunta__tipo',)
    search_fields = ['id_estudiante__nombre',]
    list_select_related = ('id_pregunta','id_exploracion','id_estudiante','opcion_seleccionada')

class EtapaCompletadaAdmin(admin.ModelAdmin):
    list_display = ('estudiante','etapa','fecha')
    list_filter = ('etapa',)
    search_fields = ('etapa__numetapa','estudiante__nombre')
    list_select_related = ('estudiante', 'etapa')

class ExploracionAdmin(admin.ModelAdmin):
    list_display = ('id_etapa','titulo','urlvideo','orden')
    list_filter = ('id_etapa',)
    search_fields = ('id_etapa__numetapa',)
    list_select_related = ('id_etapa',)

admin.site.register(TipoCaso, TipoCasoAdmin)
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Etapa, EtapaAdmin)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(OpcionMultiple,OpcionMultipleAdmin)
admin.site.register(Registro,RegistroAdmin)
admin.site.register(EtapaCompletada, EtapaCompletadaAdmin)
admin.site.register(Exploracion, ExploracionAdmin)