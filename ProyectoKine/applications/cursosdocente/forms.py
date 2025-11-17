from django import forms
from.models import Curso

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombrecurso', 'objetivos']
        widgets = {
            'nombrecurs': forms.TextInput(attrs={'class':'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'}),
            'objetivos': forms.Textarea(attrs={'class': 'form-textarea mt-1 block w-full rounded-md border-gray-300 shadow-sm', 'rows': 4}),
        }

        labels = {
            'nombrecurso': 'Nombre del Curso',
            'objetivos': 'Objetivos',

        }