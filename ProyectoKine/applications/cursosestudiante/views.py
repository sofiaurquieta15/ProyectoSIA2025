from django.shortcuts import render, redirect
import json
from django.db.models import Count
from django.views.generic import ListView, CreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from applications.cursosdocente.models import Curso
from applications.login.models import Docente, Estudiante
from applications.casospacientes.models import Paciente, Etapa, EtapaCompletada
from applications.cursosestudiante.models import Avance, Enrolamiento

class ListaCursosEstudianteView(ListView):
    model = Curso
    template_name = 'cursosestudiante/listadocursos.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        # 1. Obtenemos el ID del estudiante de la sesión
        estudiante_id = self.request.session.get('estudiante_id')
        
        if estudiante_id:
            # 2. Filtramos los cursos usando la relación inversa 'enrolamientos'
            # (definida en tu modelo Enrolamiento con related_name='enrolamientos')
            return Curso.objects.filter(enrolamientos__estudiante_id=estudiante_id)
        else:
            # Si no hay sesión de estudiante, no mostramos nada
            return Curso.objects.none()
    
def menu_estudiante(request):
    # Verifica si el usuario tiene una sesión activa
    usuario_id = request.session.get('usuario_id')  # Obtiene el ID del estudiante de la sesión

    if not usuario_id:  # Si no hay usuario_id en la sesión, redirige al login
        return redirect('login:login_estudiante')  # Redirige al login si no está autenticado

    try:
        # Intenta obtener el estudiante con el ID almacenado en la sesión
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        # Si el estudiante no existe, redirige al login
        return redirect('login:login_estudiante')

    # Si el estudiante existe, pasa el objeto a la plantilla
    return render(request, 'cursosestudiante/menuestudiante.html', {'user': usuario})

def RevisarAvancesView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login:login_estudiante')

    try:
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        return redirect('login:login_estudiante')

    # 1. Obtener cursos del estudiante
    enrolamientos = Enrolamiento.objects.filter(estudiante=usuario)
    
    cursos_data = []
    total_cursos_completados = 0
    suma_porcentajes_totales = 0

    for enrol in enrolamientos:
        curso = enrol.curso
        
        # Obtener pacientes del curso
        pacientes = Paciente.objects.filter(id_curso=curso)
        pacientes_data = []
        
        total_etapas_curso = 0
        etapas_completadas_curso = 0

        for index, paciente in enumerate(pacientes):
            # Obtener etapas del paciente
            etapas = Etapa.objects.filter(id_paciente=paciente).order_by('numetapa')
            etapas_data = []
            
            # Verificar estado de cada etapa
            for etapa in etapas:
                completada = EtapaCompletada.objects.filter(estudiante=usuario, etapa=etapa).exists()
                etapas_data.append({
                    'num': etapa.numetapa,
                    'nombre': etapa.nombreetapa,
                    'completada': completada
                })
                
                # Contadores para el porcentaje del curso
                total_etapas_curso += 1
                if completada:
                    etapas_completadas_curso += 1

            pacientes_data.append({
                'id_interno': f"c{curso.id}-p{paciente.id}", # ID único para los tabs JS
                'indice': index + 1, # Para mostrar "Paciente 1", "Paciente 2"
                'nombre': paciente.nombre,
                'etapas': etapas_data
            })

        # Calcular porcentaje del curso
        porcentaje_curso = 0
        if total_etapas_curso > 0:
            porcentaje_curso = int((etapas_completadas_curso / total_etapas_curso) * 100)
        
        if porcentaje_curso == 100:
            total_cursos_completados += 1
            
        suma_porcentajes_totales += porcentaje_curso

        cursos_data.append({
            'curso': curso,
            'porcentaje': porcentaje_curso,
            'pacientes': pacientes_data
        })

    # Calcular porcentaje general (promedio de avance de todos los cursos)
    total_cursos = len(cursos_data)
    porcentaje_general = 0
    if total_cursos > 0:
        porcentaje_general = int(suma_porcentajes_totales / total_cursos)

    return render(request, 'cursosestudiante/avances.html', {
        'cursos_data': cursos_data,
        'porcentaje_general': porcentaje_general,
        'cursos_completados_count': total_cursos_completados,
        'usuario': usuario
    })