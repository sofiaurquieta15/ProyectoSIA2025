from django import forms
from .models import Estudiante
from django.core.exceptions import ValidationError
from django.views.generic.edit import FormView, CreateView

class LoginForm(forms.Form):
    correo = forms.EmailField(
        label="Correo Electrónico",
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Nombre de usuario (correo)',
            'class':'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-800 focus:border-blue-800 text-gray-700'

        })
    )
    password = forms.CharField(
        label="Contraseña",
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder':'Contraseña',
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-800 focus:border-blue-800 text-gray-700'
        })
    )

class RegistroEstudianteForm(forms.ModelForm):
    nombre = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Tu nombre'})
    )
    apellido = forms.CharField(
        label="Apellido",
        widget=forms.TextInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Tu apellido'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Contraseña', 'id': 'id_reg_password'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'Repite la contraseña', 'id': 'id_reg_confirm'})
    )

    class Meta:
        model = Estudiante
        fields = ['nombre', 'apellido', 'correo_institucional']
        widgets = {
            'correo_institucional': forms.EmailInput(attrs={'class': 'w-full p-3 border border-gray-300 rounded-lg', 'placeholder': 'ejemplo@alumnos.ucn.cl'}),
        }

    def clean_correo_institucional(self):
        correo = self.cleaned_data.get('correo_institucional')
        # 1. Validar dominio
        if not correo.endswith('@alumnos.ucn.cl'):
            raise ValidationError("El correo debe terminar en @alumnos.ucn.cl")
        
        # 2. Validar que no exista
        if Estudiante.objects.filter(correo_institucional=correo).exists():
            raise ValidationError("Este correo ya está registrado.")
            
        return correo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Las contraseñas no coinciden.")
        return cleaned_data