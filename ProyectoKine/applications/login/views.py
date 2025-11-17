from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView
from .models import Estudiante, Docente
from .forms import LoginForm
from django.urls import reverse_lazy, reverse
# Create your views here.

class InicioLoginView(TemplateView):
    template_name = 'base_site.html'

class LoginView(FormView):
    template_name = 'login/login.html'
    form_class = LoginForm
    #success_url = reverse_lazy('cursos:lista_cursos')
    rol = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rol'] = self.rol
        return context
    
    def form_valid(self, form):
        correo = form.cleaned_data['correo']
        password = form.cleaned_data['password']

        usuario = None
        if self.rol == "Estudiante":
            try:
                estudiante = Estudiante.objects.get(correo_institucional=correo)
                if estudiante.passw_estudiante == password:
                    usuario = estudiante
            except Estudiante.DoesNotExist:
                pass
        elif self.rol == "Docente":
            try:
                docente = Docente.objects.get(correo_docente=correo)
                if docente.passw_docente == password:
                    usuario = docente
            except Docente.DoesNotExist:
                pass
        
        if usuario is not None:
            login(self.request, usuario)
            self.request.session['rol'] = self.rol
            print(f'Login exitoso para {self.rol}:{correo}')
            if self.rol == 'Estudiante':
                return redirect(reverse('cursos:lista_cursos'))
            elif self.rol == 'Docente':
                return redirect(reverse('cursos:listado_cursos'))
            
            return redirect(reverse('cursos:lista_cursos')) 
        else:
            form.add_error(None, 'Correo o contraseña incorrectos.')
            return self.form_invalid(form)

class LoginEstudianteView(LoginView):
    rol = 'Estudiante'
    
        

class LoginDocenteView(LoginView):
    rol = 'Docente'
