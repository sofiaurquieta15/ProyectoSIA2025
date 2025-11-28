from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Curso
from .forms import CursoForm
from applications.login.models import Docente

class ListaCursosEstudianteView(ListView):
    model = Curso
    template_name = 'cursosestudiante/listadocursos.html'
    context_object_name = 'object_list'