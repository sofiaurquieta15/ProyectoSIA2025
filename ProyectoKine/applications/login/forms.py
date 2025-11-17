from django import forms

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