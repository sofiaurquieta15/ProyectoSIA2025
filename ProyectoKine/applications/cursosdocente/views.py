from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Curso
from .forms import CursoForm
from applications.login.models import Docente

class ListaCursosEstudianteView(ListView):
    model = Curso
    template_name = 'cursos/listadocursos.html'
    context_object_name = 'object_list'

class ListaCursosView(ListView):
    model = Curso
    template_name = 'cursos/vistacursosdocente.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        if self.request.session.get('rol') == 'Docente':
            try:
                docente = Docente.objects.get(correo_docente=self.request.user.correo_docente)
                return Curso.objects.filter(docente=docente)
            except Docente.DoesNotExist:
                return Curso.objects.none()
            except AttributeError:
                return Curso.objects.none()
        elif self.request.session.get('rol') == 'Estudiante':
            return Curso.objects.all()
        return Curso.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rol'] = self.request.session.get('rol')
        return context
    

class CursoCreateView(LoginRequiredMixin,UserPassesTestMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'cursos/crearcursos.html'
    success_url = reverse_lazy('cursos:lista_cursos')

    def test_func(self):
        return self.request.session.get('rol') == 'Docente'
    
    def form_valid(self, form):
        if self.request.session.get('rol') == 'Docente':
            try:
                docente = Docente.objects.get(correo_docente=self.request.user.correo_docente)
                form.instance.docente = docente
            except Docente.DoesNotExist:
                form.add_error(None, "No se pudo asocial el curso a un docente válido.")
                return self.form_invalid(form)
        return super().form_valid(form)

