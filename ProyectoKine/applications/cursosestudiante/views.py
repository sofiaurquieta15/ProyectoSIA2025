import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

# Importación de Modelos EXTERNOS
from applications.cursosdocente.models import Curso
from applications.login.models import Estudiante
from applications.casospacientes.models import Paciente, Etapa, EtapaCompletada, Exploracion

# Importación de Modelos PROPIOS
from applications.cursosestudiante.models import Avance, Enrolamiento, SolicitudRevision

class ListaCursosEstudianteView(ListView):
    model = Curso
    template_name = 'cursosestudiante/listadocursos.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        estudiante_id = self.request.session.get('estudiante_id')
        if estudiante_id:
            return Curso.objects.filter(enrolamientos__estudiante_id=estudiante_id)
        else:
            return Curso.objects.none()
    
def menu_estudiante(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login:login_estudiante')
    try:
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        return redirect('login:login_estudiante')
    return render(request, 'cursosestudiante/menuestudiante.html', {'user': usuario})

def RevisarAvancesView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login:login_estudiante')
    try:
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        return redirect('login:login_estudiante')

    enrolamientos = Enrolamiento.objects.filter(estudiante=usuario)
    cursos_data = []
    total_cursos_completados = 0
    suma_porcentajes_totales = 0

    for enrol in enrolamientos:
        curso = enrol.curso
        pacientes = Paciente.objects.filter(id_curso=curso)
        pacientes_data = []
        
        total_etapas_curso = 0
        etapas_completadas_curso = 0

        for index, paciente in enumerate(pacientes):
            etapas = Etapa.objects.filter(id_paciente=paciente).order_by('numetapa')
            etapas_data = []
            
            for etapa in etapas:
                completada = EtapaCompletada.objects.filter(estudiante=usuario, etapa=etapa).exists()
                etapas_data.append({
                    'num': etapa.numetapa,
                    'nombre': etapa.nombreetapa,
                    'completada': completada
                })
                
                total_etapas_curso += 1
                if completada:
                    etapas_completadas_curso += 1

            pacientes_data.append({
                'id_interno': f"c{curso.id}-p{paciente.id}",
                'indice': index + 1,
                'nombre': paciente.nombre,
                'id': paciente.id,
                'etapas': etapas_data
            })

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

# ==========================================
# SECCIÓN: SOLICITUD DE REVISIÓN
# ==========================================

def SolicitudRevisionView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login:login_estudiante')

    try:
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        return redirect('login:login_estudiante')

    # 1. Obtener IDs de exploraciones PENDIENTES (Etapa 2)
    exploraciones_pendientes_ids = SolicitudRevision.objects.filter(
        estudiante=usuario,
        estado='PENDIENTE',
        etapa_solicitud=2, 
        exploracion_especifica__isnull=False
    ).values_list('exploracion_especifica_id', flat=True)

    # 2. NUEVO: Obtener IDs de pacientes con DIAGNÓSTICO PENDIENTE (Etapa 3)
    pacientes_diagnostico_pendiente_ids = SolicitudRevision.objects.filter(
        estudiante=usuario,
        estado='PENDIENTE',
        etapa_solicitud=3
    ).values_list('paciente_id', flat=True)

    enrolamientos = Enrolamiento.objects.filter(estudiante=usuario)
    cursos_data = []

    for enrol in enrolamientos:
        curso = enrol.curso
        pacientes_curso = Paciente.objects.filter(id_curso=curso)
        
        pacientes_validos = []
        
        for p in pacientes_curso:
            completadas = EtapaCompletada.objects.filter(estudiante=usuario, etapa__id_paciente=p).values_list('etapa__numetapa', flat=True)
            
            if 2 in completadas or 3 in completadas:
                # Filtrar exploraciones para Etapa 2
                exploraciones_obj = Exploracion.objects.filter(id_etapa__id_paciente=p).exclude(id__in=exploraciones_pendientes_ids)
                lista_exploraciones = [{'id': e.id, 'titulo': e.titulo} for e in exploraciones_obj]

                # Verificar si tiene diagnóstico pendiente
                tiene_diagnostico_pendiente = (p.id in pacientes_diagnostico_pendiente_ids)

                pacientes_validos.append({
                    'id': p.id,
                    'nombre': p.nombre,
                    'etapas_completadas': list(completadas),
                    'exploraciones': lista_exploraciones,
                    'tiene_diagnostico_pendiente': tiene_diagnostico_pendiente  # <--- DATO NUEVO ENVIADO AL FRONTEND
                })

        if pacientes_validos:
            cursos_data.append({
                'id': curso.id,
                'nombre': curso.nombrecurso,
                'pacientes': pacientes_validos
            })

    return render(request, 'cursosestudiante/solicitar_revision.html', {
        'data_json': json.dumps(cursos_data),
        'usuario': usuario
    })

@csrf_exempt
def crear_solicitud_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            usuario_id = request.session.get('usuario_id')
            usuario = Estudiante.objects.get(id=usuario_id)
            
            curso_id = data.get('curso_id')
            paciente_id = data.get('paciente_id')
            etapa_num = int(data.get('etapa_num')) 
            motivo = data.get('motivo')
            exploracion_id = data.get('exploracion_id')

            # Validación Backend de Diagnóstico Duplicado
            if etapa_num == 3:
                existe = SolicitudRevision.objects.filter(
                    estudiante=usuario,
                    paciente_id=paciente_id,
                    etapa_solicitud=3,
                    estado='PENDIENTE'
                ).exists()
                if existe:
                    return JsonResponse({'ok': False, 'error': 'Ya tienes una solicitud de diagnóstico pendiente para este paciente.'})

            curso = Curso.objects.get(id=curso_id)
            paciente = Paciente.objects.get(id=paciente_id)
            
            nueva_solicitud = SolicitudRevision(
                estudiante=usuario,
                curso=curso,
                paciente=paciente,
                etapa_solicitud=etapa_num,
                motivo=motivo,
                estado='PENDIENTE'
            )
            
            if exploracion_id:
                existe_duplicada = SolicitudRevision.objects.filter(
                    estudiante=usuario,
                    exploracion_especifica_id=exploracion_id,
                    estado='PENDIENTE'
                ).exists()
                
                if existe_duplicada:
                     return JsonResponse({'ok': False, 'error': 'Ya tienes una solicitud pendiente para esta exploración.'})

                nueva_solicitud.exploracion_especifica = Exploracion.objects.get(id=exploracion_id)
                
            nueva_solicitud.save()
            
            return JsonResponse({'ok': True, 'msg': 'Solicitud enviada correctamente.'})
            
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def EstadoSolicitudesView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login:login_estudiante')

    try:
        usuario = Estudiante.objects.get(id=usuario_id)
    except Estudiante.DoesNotExist:
        return redirect('login:login_estudiante')

    # 1. Consulta Base (Todas las solicitudes del alumno)
    solicitudes = SolicitudRevision.objects.filter(estudiante=usuario).order_by('-fecha_solicitud')

    # 2. Obtener opciones para los filtros (Solo cursos/pacientes presentes en sus solicitudes)
    # Usamos distinct para no repetir opciones en el dropdown
    cursos_ids = solicitudes.values_list('curso_id', flat=True).distinct()
    pacientes_ids = solicitudes.values_list('paciente_id', flat=True).distinct()
    
    cursos_filter = Curso.objects.filter(id__in=cursos_ids)
    pacientes_filter = Paciente.objects.filter(id__in=pacientes_ids)

    # 3. Aplicar Filtros si vienen en la URL (GET)
    curso_id = request.GET.get('curso')
    paciente_id = request.GET.get('paciente')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo') # 2=Exploración, 3=Diagnóstico

    if curso_id:
        solicitudes = solicitudes.filter(curso_id=curso_id)
    
    if paciente_id:
        solicitudes = solicitudes.filter(paciente_id=paciente_id)
    
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
        
    if tipo:
        solicitudes = solicitudes.filter(etapa_solicitud=tipo)

    context = {
        'solicitudes': solicitudes,
        'cursos_filter': cursos_filter,
        'pacientes_filter': pacientes_filter,
        # Enviamos lo seleccionado para mantener el valor en el input
        'selected_curso': int(curso_id) if curso_id else '',
        'selected_paciente': int(paciente_id) if paciente_id else '',
        'selected_estado': estado or '',
        'selected_tipo': int(tipo) if tipo else '',
    }

    return render(request, 'cursosestudiante/estado_solicitudes.html', context)