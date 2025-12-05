from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView
from .models import Estudiante, Docente
from .forms import LoginForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib import messages

# Create your views here.

class InicioLoginView(TemplateView):
    template_name = 'base_site.html'

class LoginView(FormView):
    template_name = 'login/login.html'
    form_class = LoginForm
    rol = None  # Se define en las subclases

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rol'] = self.rol
        return context

    def form_valid(self, form):
        correo = form.cleaned_data['correo']
        password = form.cleaned_data['password']

        usuario = None

        # Autenticación según rol
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

        # Si credenciales válidas
        if usuario is not None:
            login(self.request, usuario)
            self.request.session['usuario_id'] = usuario.id
            self.request.session['rol'] = self.rol

            # Obtener el parámetro 'next' de la URL para redirigir al usuario
            next_url = self.request.GET.get('next', None)

            # Redirigir según el rol
            if next_url:
                return redirect(next_url)  # Si next está presente, redirigir a esa URL

            # Redirigir a menu estudiante para estudiantes
            if self.rol == 'Estudiante':
                self.request.session['estudiante_id'] = usuario.id
                return redirect('cursosestudiante:menu_estudiante')

            # CAMBIO AQUÍ: Docente → Menú Docente
            if self.rol == 'Docente':
                return redirect('cursos:menu_docente')

            # fallback
            return redirect('cursos:menu_docente')

        # Si falló autenticación
        form.add_error(None, 'Correo o contraseña incorrectos.')
        return self.form_invalid(form)


class LoginEstudianteView(LoginView):
    rol = 'Estudiante'


class LoginDocenteView(LoginView):
    rol = 'Docente'


def logout_view(request):
    logout(request)  # Elimina la sesión del usuario
    return redirect(reverse('login:inicio'))

@require_POST
def editar_perfil_docente(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id or request.session.get('rol') != 'Docente':
        return redirect('login:login_docente')

    try:
        docente = Docente.objects.get(id=usuario_id)
        tipo_accion = request.POST.get('tipo_accion') # 'info' o 'password'

        # --- CASO 1: ACTUALIZAR INFORMACIÓN BÁSICA ---
        if tipo_accion == 'info':
            pass_confirmacion = request.POST.get('password_validacion')
            
            # Validar contraseña actual obligatoria
            if docente.passw_docente != pass_confirmacion:
                messages.error(request, "La contraseña es incorrecta", extra_tags='error_pass_info')
            else:
                # Guardar cambios
                docente.nombre_docente = request.POST.get('nombre')
                docente.apellido_docente = request.POST.get('apellido')
                docente.correo_docente = request.POST.get('correo') 
                docente.save()
                messages.success(request, "Datos actualizados correctamente")

        # --- CASO 2: CAMBIAR CONTRASEÑA ---
        elif tipo_accion == 'password':
            pass_actual = request.POST.get('password_actual')
            pass_nueva = request.POST.get('password_nueva')
            pass_confirm = request.POST.get('password_confirm')

            error = False
            
            # 1. Validar contraseña actual
            if docente.passw_docente != pass_actual:
                messages.error(request, "La contraseña es incorrecta", extra_tags='error_pass_actual_cambio')
                error = True
            
            # 2. Validar coincidencia de nuevas
            if pass_nueva != pass_confirm:
                messages.error(request, "Las contraseñas no coinciden", extra_tags='error_pass_match')
                error = True

            if not error:
                docente.passw_docente = pass_nueva
                docente.save()
                messages.success(request, "Contraseña cambiada con éxito")

    except Docente.DoesNotExist:
        pass

    return redirect('cursos:menu_docente')

@require_POST
def editar_perfil_estudiante(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id or request.session.get('rol') != 'Estudiante':
        return redirect('login:login_estudiante')

    try:
        estudiante = Estudiante.objects.get(id=usuario_id)
        tipo_accion = request.POST.get('tipo_accion')

        # --- CASO 1: ACTUALIZAR DATOS ---
        if tipo_accion == 'info':
            pass_confirmacion = request.POST.get('password_validacion')
            
            if estudiante.passw_estudiante != pass_confirmacion:
                messages.error(request, "La contraseña es incorrecta", extra_tags='error_pass_info')
            else:
                estudiante.nombre = request.POST.get('nombre')
                estudiante.apellido = request.POST.get('apellido')
                estudiante.correo_institucional = request.POST.get('correo')
                estudiante.save()
                messages.success(request, "Datos actualizados correctamente")

        # --- CASO 2: CAMBIAR CONTRASEÑA ---
        elif tipo_accion == 'password':
            pass_actual = request.POST.get('password_actual')
            pass_nueva = request.POST.get('password_nueva')
            pass_confirm = request.POST.get('password_confirm')

            error = False
            if estudiante.passw_estudiante != pass_actual:
                messages.error(request, "La contraseña es incorrecta", extra_tags='error_pass_actual_cambio')
                error = True
            
            if pass_nueva != pass_confirm:
                messages.error(request, "Las contraseñas no coinciden", extra_tags='error_pass_match')
                error = True

            if not error:
                estudiante.passw_estudiante = pass_nueva
                estudiante.save()
                messages.success(request, "Contraseña cambiada con éxito")

    except Estudiante.DoesNotExist:
        pass

    return redirect('cursosestudiante:menu_estudiante')