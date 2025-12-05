from django import forms
from applications.cursosdocente.models import Curso
from applications.casospacientes.models import Paciente, TipoCaso, Etapa, Pregunta, Exploracion

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombrecurso', 'objetivos']
        widgets = {
            'nombrecurso': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'objetivos': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 3}),
        }

class TipoCasoForm(forms.ModelForm):
    class Meta:
        model = TipoCaso
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Ej: Traumatología'})
        }

class PacienteForm(forms.ModelForm):
    # Campo extra para mostrar el botón de "Nuevo Tipo"
    nuevo_tipo_caso = forms.BooleanField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Paciente
        fields = ['nombre', 'edad', 'sexo', 'ocupacion', 'descripcion', 'tipo_caso', 'id_curso']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'edad': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'sexo': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'ocupacion': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 3}),
            'tipo_caso': forms.Select(attrs={'class': 'w-full p-2 border rounded', 'id': 'select-tipo-caso'}),
            'id_curso': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar cursos solo del docente logueado
        self.fields['id_curso'].queryset = Curso.objects.filter(id_docente=user)