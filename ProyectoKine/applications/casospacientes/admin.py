from django.contrib import admin
from .models import *

class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombreetapa', 'numetapa', 'id_paciente', 'urlvideo')
    list_filter = ('id_paciente',) #agrega un filtro, por paciente para facilitar la búsqueda
    search_fields = ('nombreetapa',) 

admin.site.register(TipoCaso)
admin.site.register(Paciente)
admin.site.register(Etapa, EtapaAdmin)
admin.site.register(Pregunta)
admin.site.register(OpcionMultiple)
admin.site.register(Registro)
