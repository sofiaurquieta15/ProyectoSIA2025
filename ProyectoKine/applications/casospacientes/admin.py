import json
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from .models import *

# ==========================================
# 1. FORMULARIOS PERSONALIZADOS
# ==========================================

class PreguntaForm(forms.ModelForm):
    paciente_seleccionado = forms.ModelChoiceField(
        queryset=Paciente.objects.all(),
        label="Seleccionar Paciente",
        help_text="La pregunta se asociará automáticamente a la Etapa 1 o 3 de este paciente."
    )

    TIPO_ETAPA_PREGUNTA = [
        ('MULTIPLE', 'Etapa 1: Selección Múltiple'),
        ('ESCRITA', 'Etapa 3: Diagnóstico/Escrita'),
    ]
    
    destino_etapa = forms.ChoiceField(
        choices=TIPO_ETAPA_PREGUNTA,
        label="¿A qué etapa pertenece?",
        help_text="Selecciona si esta pregunta es para la Etapa 1 o la Etapa 3."
    )

    class Meta:
        model = Pregunta
        fields = '__all__'
        exclude = ('id_etapa', 'clave_respuesta_escrita')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.id_etapa:
            self.fields['paciente_seleccionado'].initial = self.instance.id_etapa.id_paciente
            self.fields['destino_etapa'].initial = self.instance.id_etapa.tipo_pregunta

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente_seleccionado')
        tipo_seleccionado = cleaned_data.get('destino_etapa')

        if paciente and tipo_seleccionado:
            try:
                etapa_destino = Etapa.objects.get(
                    id_paciente=paciente, 
                    tipo_pregunta=tipo_seleccionado
                )
            except Etapa.DoesNotExist:
                nombre_etapa = "Etapa 1" if tipo_seleccionado == 'MULTIPLE' else "Etapa 3"
                raise ValidationError(f"El paciente {paciente.nombre} no tiene creada la '{nombre_etapa}'.")
            except Etapa.MultipleObjectsReturned:
                raise ValidationError(f"Error: El paciente tiene etapas duplicadas.")

            self.instance.id_etapa = etapa_destino
            self.instance.tipo = tipo_seleccionado

            qs = Pregunta.objects.filter(id_etapa=etapa_destino)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            cantidad = qs.count()

            if tipo_seleccionado == 'MULTIPLE' and cantidad >= 5:
                raise ValidationError(f"Error: La Etapa 1 ya tiene 5 preguntas.")
            elif tipo_seleccionado == 'ESCRITA' and cantidad >= 1:
                raise ValidationError(f"Error: La Etapa 3 ya tiene una pregunta.")

        return cleaned_data

class ExploracionForm(forms.ModelForm):
    paciente_seleccionado = forms.ModelChoiceField(
        queryset=Paciente.objects.all(),
        label="Seleccionar Paciente",
        help_text="Se asociará a la 'Etapa 2: Exploraciones'."
    )

    class Meta:
        model = Exploracion
        fields = '__all__'
        exclude = ('id_etapa', 'orden')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.id_etapa:
            self.fields['paciente_seleccionado'].initial = self.instance.id_etapa.id_paciente

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente_seleccionado')

        if paciente:
            try:
                etapa_destino = Etapa.objects.get(id_paciente=paciente, tipo_pregunta='EXPLORACIONES')
            except Etapa.DoesNotExist:
                raise ValidationError(f"El paciente {paciente.nombre} no tiene creada la 'Etapa 2'.")
            
            self.instance.id_etapa = etapa_destino
            
            qs = Exploracion.objects.filter(id_etapa=etapa_destino)
            if self.instance.pk: qs = qs.exclude(pk=self.instance.pk)
            
            if qs.count() >= 6:
                raise ValidationError(f"Error: Límite de 6 exploraciones alcanzado.")
            
            if not self.instance.pk:
                self.instance.orden = qs.count() + 1

        return cleaned_data


# ==========================================
# 2. ADMINS
# ==========================================

class TipoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ['nombre',]

class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nombre','edad','sexo','tipo_caso','id_curso')
    list_filter = ('tipo_caso__nombre', 'id_curso__nombrecurso') 
    search_fields = ('nombre', 'id_curso__nombrecurso')
    list_select_related = ('tipo_caso','id_curso')

class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombreetapa', 'numetapa', 'id_paciente','tipo_pregunta')
    list_filter = ('id_paciente','tipo_pregunta')
    search_fields = ('nombreetapa', 'id_paciente__nombre')
    list_select_related = ('id_paciente',)

class PreguntaAdmin(admin.ModelAdmin):
    form = PreguntaForm
    # CAMBIO AQUÍ: Se eliminó 'texto' de la lista de campos
    fields = ('paciente_seleccionado', 'destino_etapa', 'titulo', 'urlvideo', 'retroalimentacion_general', 'docente')
    
    list_display = ('get_paciente_nombre', 'titulo', 'tipo', 'urlvideo')
    list_filter = ('tipo', 'id_etapa__id_paciente')
    search_fields = ('titulo', 'id_etapa__id_paciente__nombre')
    list_select_related = ('docente', 'id_etapa', 'id_etapa__id_paciente')

    def get_paciente_nombre(self, obj):
        return obj.id_etapa.id_paciente.nombre
    get_paciente_nombre.short_description = "Paciente"

class OpcionMultipleAdmin(admin.ModelAdmin):
    list_display = ('get_paciente', 'pregunta', 'texto_opcion', 'is_correct')
    list_filter = ('is_correct', 'pregunta__id_etapa__id_paciente')
    search_fields = ('pregunta__titulo', 'texto_opcion')
    list_select_related = ('pregunta', 'pregunta__id_etapa__id_paciente')

    def get_paciente(self, obj):
        return obj.pregunta.id_etapa.id_paciente.nombre
    get_paciente.short_description = "Paciente"

class RegistroAdmin(admin.ModelAdmin):
    list_display = ('mostrar_contenido', 'get_paciente', 'id_estudiante', 'fecha_envio')
    list_filter = ('id_pregunta__tipo',)
    search_fields = ['id_estudiante__nombre', 'id_estudiante__correo_institucional']
    list_select_related = (
        'id_pregunta', 'id_pregunta__id_etapa', 'id_pregunta__id_etapa__id_paciente',
        'id_exploracion', 'id_exploracion__id_etapa', 'id_exploracion__id_etapa__id_paciente',
        'id_estudiante', 'opcion_seleccionada'
    )

    def mostrar_contenido(self, obj):
        if obj.id_pregunta: return f"[Pregunta] {obj.id_pregunta.titulo}"
        elif obj.id_exploracion: return f"[Exploración] {obj.id_exploracion.titulo}"
        return "-"
    mostrar_contenido.short_description = "Item Evaluado"

    def get_paciente(self, obj):
        if obj.id_pregunta: return obj.id_pregunta.id_etapa.id_paciente.nombre
        elif obj.id_exploracion: return obj.id_exploracion.id_etapa.id_paciente.nombre
        return "-"
    get_paciente.short_description = "Paciente"

class EtapaCompletadaAdmin(admin.ModelAdmin):
    list_display = ('estudiante','etapa','fecha')
    list_filter = ('etapa',)
    search_fields = ('etapa__numetapa','estudiante__nombre')
    list_select_related = ('estudiante', 'etapa')

class ExploracionAdmin(admin.ModelAdmin):
    form = ExploracionForm
    fields = ('paciente_seleccionado', 'titulo', 'instruccion', 'urlvideo', 'retroalimentacion_general')
    list_display = ('get_paciente_nombre', 'titulo', 'orden', 'urlvideo')
    list_filter = ('id_etapa__id_paciente',)
    search_fields = ('titulo', 'id_etapa__id_paciente__nombre')
    list_select_related = ('id_etapa', 'id_etapa__id_paciente')

    def get_paciente_nombre(self, obj):
        return obj.id_etapa.id_paciente.nombre
    get_paciente_nombre.short_description = "Paciente"
    get_paciente_nombre.admin_order_field = 'id_etapa__id_paciente__nombre'

# ==========================================
# 3. REGISTRO DE ADMINS
# ==========================================
admin.site.register(TipoCaso, TipoCasoAdmin)
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Etapa, EtapaAdmin)
admin.site.register(Pregunta, PreguntaAdmin)
admin.site.register(OpcionMultiple,OpcionMultipleAdmin)
admin.site.register(Registro,RegistroAdmin)
admin.site.register(EtapaCompletada, EtapaCompletadaAdmin)
admin.site.register(Exploracion, ExploracionAdmin)