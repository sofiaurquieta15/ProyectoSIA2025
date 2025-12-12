import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from applications.cursosdocente.models import Curso
from applications.login.models import Estudiante
from applications.casospacientes.models import Paciente, Etapa, EtapaCompletada, Exploracion
from applications.cursosestudiante.models import Avance, Enrolamiento, SolicitudRevision, NotificacionVista

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

def MenuEstudianteView(request):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id: return redirect('login:login_estudiante')
    
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist: return redirect('login:login_estudiante')

    vistas = NotificacionVista.objects.filter(estudiante=estudiante).values_list('tipo', 'referencia_id')
    vistas_set = {f"{v[0]}_{v[1]}" for v in vistas}

    notificaciones_lista = []
    solicitudes = SolicitudRevision.objects.filter(
        estudiante=estudiante, estado='RESPONDIDA'
    ).select_related('curso', 'curso__id_docente', 'paciente').order_by('-fecha_respuesta')[:10]

    for sol in solicitudes:
        uid_logico = f"SOLICITUD_{sol.id}"
        es_leido = uid_logico in vistas_set

        link = f"/cursosestudiante/estado-solicitudes/?curso={sol.curso.id}&paciente={sol.paciente.id}&tipo={sol.etapa_solicitud}&estado=RESPONDIDA"
        
        docente = sol.curso.id_docente
        notificaciones_lista.append({
            'tipo_obj': 'SOLICITUD',
            'id_obj': sol.id,            
            'leido': es_leido,
            
            # Datos visuales
            'tipo_icono': 'RESPUESTA_SOLICITUD',
            'categoria': sol.get_etapa_solicitud_display(),
            'docente_nombre': f"{docente.nombre_docente} {docente.apellido_docente}",
            'curso_nombre': sol.curso.nombrecurso,
            'mensaje': f"Respuesta para el paciente {sol.paciente.nombre}",
            'url': link,
            'fecha': sol.fecha_respuesta,
        })

    mis_cursos_ids = Enrolamiento.objects.filter(estudiante=estudiante).values_list('curso_id', flat=True)
    pacientes = Paciente.objects.filter(
        id_curso__id__in=mis_cursos_ids, visible=True
    ).select_related('id_curso', 'id_curso__id_docente').order_by('-id')[:10]

    for pac in pacientes:
        uid_logico = f"PACIENTE_{pac.id}"
        es_leido = uid_logico in vistas_set

        docente = pac.id_curso.id_docente
        notificaciones_lista.append({
            'tipo_obj': 'PACIENTE',
            'id_obj': pac.id,
            'leido': es_leido,

            'tipo_icono': 'NUEVO_PACIENTE',
            'categoria': 'Nuevo Caso',
            'docente_nombre': f"{docente.nombre_docente} {docente.apellido_docente}",
            'curso_nombre': pac.id_curso.nombrecurso,
            'mensaje': f"Nuevo caso disponible: {pac.nombre}",
            'url': '/cursosestudiante/mis-cursos/',
            'fecha': None,
        })

    notificaciones_lista.sort(key=lambda x: x['leido']) 
    
    notificaciones_lista = notificaciones_lista[:10]

    count_no_leidas = sum(1 for n in notificaciones_lista if not n['leido'])

    context = {
        'user': estudiante,
        'notificaciones': notificaciones_lista,
        'count_no_leidas': count_no_leidas
    }
    return render(request, 'cursosestudiante/menuestudiante.html', context)

# --- NUEVA FUNCIÓN AJAX ---
@csrf_exempt
def marcar_notificacion_vista(request):
    if request.method == 'POST':
        estudiante_id = request.session.get('estudiante_id')
        if not estudiante_id: return JsonResponse({'ok': False})
        
        try:
            estudiante = Estudiante.objects.get(id=estudiante_id)
            import json
            data = json.loads(request.body)
            tipo = data.get('tipo')
            ref_id = data.get('id')
            
            NotificacionVista.objects.get_or_create(
                estudiante=estudiante,
                tipo=tipo,
                referencia_id=ref_id
            )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

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

        pacientes = Paciente.objects.filter(id_curso=curso, visible=True)

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

    exploraciones_pendientes_ids = SolicitudRevision.objects.filter(
        estudiante=usuario,
        estado='PENDIENTE',
        etapa_solicitud=2, 
        exploracion_especifica__isnull=False
    ).values_list('exploracion_especifica_id', flat=True)

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
                    'tiene_diagnostico_pendiente': tiene_diagnostico_pendiente  
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

    solicitudes = SolicitudRevision.objects.filter(estudiante=usuario).order_by('-fecha_solicitud')

    cursos_ids = solicitudes.values_list('curso_id', flat=True).distinct()
    pacientes_ids = solicitudes.values_list('paciente_id', flat=True).distinct()
    
    cursos_filter = Curso.objects.filter(id__in=cursos_ids)
    pacientes_filter = Paciente.objects.filter(id__in=pacientes_ids)

    curso_id = request.GET.get('curso')
    paciente_id = request.GET.get('paciente')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

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
        'selected_curso': int(curso_id) if curso_id else '',
        'selected_paciente': int(paciente_id) if paciente_id else '',
        'selected_estado': estado or '',
        'selected_tipo': int(tipo) if tipo else '',
    }

    return render(request, 'cursosestudiante/estado_solicitudes.html', context)