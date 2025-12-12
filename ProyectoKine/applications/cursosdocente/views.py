import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction

# Formularios
from .forms import CursoForm, PacienteForm, TipoCasoForm

# Modelos
from applications.login.models import Docente, Estudiante
from .models import Curso
from applications.cursosestudiante.models import Enrolamiento, SolicitudRevision
from applications.cursosdocente.models import NotificacionDocenteVista
from applications.casospacientes.models import (
    Paciente, TipoCaso, Etapa, EtapaCompletada, Registro, 
    Pregunta, Exploracion, OpcionMultiple
)

def MenuDocenteView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login:login_docente')
    
    try:
        docente = Docente.objects.get(id=usuario_id)
    except Docente.DoesNotExist: return redirect('login:login_docente')

    vistas_ids = set(NotificacionDocenteVista.objects.filter(docente=docente).values_list('solicitud_id', flat=True))

    requests_qs = SolicitudRevision.objects.filter(
        curso__id_docente=docente
    ).select_related('estudiante', 'paciente', 'curso').order_by('-fecha_solicitud')[:10] 

    notificaciones = []
    for req in requests_qs:
        es_leido = req.id in vistas_ids
        
        notificaciones.append({
            'id': req.id,
            'estudiante_nombre': f"{req.estudiante.nombre} {req.estudiante.apellido}",
            'categoria': req.get_etapa_solicitud_display(), # Exploración / Diagnóstico
            'paciente_nombre': req.paciente.nombre,
            'curso_nombre': req.curso.nombrecurso,
            'fecha': req.fecha_solicitud,
            'leido': es_leido,
            'etapa_num': req.etapa_solicitud,
            
            'url_params': f"curso={req.curso.id}&estudiante={req.estudiante.id}&paciente={req.paciente.id}&etapa={req.etapa_solicitud}"
        })

    notificaciones.sort(key=lambda x: x['leido']) 
    
    notificaciones = notificaciones[:5]

    count_no_leidas = sum(1 for n in notificaciones if not n['leido'])

    return render(request, 'cursosdocente/menudocente.html', {
        'user': docente,
        'notificaciones': notificaciones,
        'count_no_leidas': count_no_leidas
    })

# --- API AJAX PARA MARCAR COMO LEÍDO ---
@csrf_exempt
def marcar_notificacion_docente(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        if not usuario_id: return JsonResponse({'ok': False})
        
        try:
            docente = Docente.objects.get(id=usuario_id)
            data = json.loads(request.body)
            sol_id = data.get('id')
            
            NotificacionDocenteVista.objects.get_or_create(
                docente=docente,
                solicitud_id=sol_id
            )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

def GestionCursosDocenteView(request):
    # 1. Validar Docente
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login:login_docente')
    
    try:
        docente = Docente.objects.get(id=usuario_id)
    except Docente.DoesNotExist:
        return redirect('login:login_docente')

    # 2. Obtener Cursos
    cursos = Curso.objects.filter(id_docente=docente)
    
    # 3. Curso Activo
    curso_id_activo = request.GET.get('curso_id')
    curso_activo = None
    
    if curso_id_activo:
        curso_activo = cursos.filter(id=curso_id_activo).first()
    elif cursos.exists():
        curso_activo = cursos.first()
        
    # 4. Datos Estudiantes y Estadísticas
    estudiantes_data = []
    
    # Variables para el Dashboard Global
    curso_stats = {
        'porcentaje_global': 0,
        'total_estudiantes': 0,
        'completados': 0
    }
    pacientes_global_stats = []
    
    if curso_activo:
        enrolamientos = Enrolamiento.objects.filter(curso=curso_activo).select_related('estudiante')
        total_estudiantes = enrolamientos.count()
        curso_stats['total_estudiantes'] = total_estudiantes

        pacientes_curso = Paciente.objects.filter(id_curso=curso_activo, visible=True)
        for enrol in enrolamientos:
            est = enrol.estudiante
            
            total_etapas = 0
            etapas_completadas = 0
            pacientes_info = []
            
            for paciente in pacientes_curso:
                etapas = Etapa.objects.filter(id_paciente=paciente).order_by('numetapa')
                etapas_info_p = []
                
                for etapa in etapas:
                    hecha = EtapaCompletada.objects.filter(estudiante=est, etapa=etapa).exists()
                    
                    etapas_info_p.append({
                        'id': etapa.id,
                        'num': etapa.numetapa,
                        'nombre': etapa.nombreetapa,
                        'completada': hecha
                    })
                    
                    total_etapas += 1
                    if hecha: etapas_completadas += 1
                
                pacientes_info.append({
                    'nombre': paciente.nombre,
                    'etapas': etapas_info_p,
                    'estudiante_id': est.id
                })
            
            porcentaje = 0
            if total_etapas > 0:
                porcentaje = int((etapas_completadas / total_etapas) * 100)
            
            # Contar para el global si el alumno terminó todo lo visible (100%)
            if porcentaje == 100 and total_etapas > 0:
                curso_stats['completados'] += 1

            estudiantes_data.append({
                'obj': est,
                'porcentaje': porcentaje,
                'pacientes': pacientes_info, 
                'json_id': f"data-est-{est.id}"
            })

        # --- B. CALCULAR ESTADÍSTICAS GLOBALES DEL CURSO ---
        if total_estudiantes > 0:
            curso_stats['porcentaje_global'] = int((curso_stats['completados'] / total_estudiantes) * 100)

        # --- C. CALCULAR ESTADÍSTICAS POR PACIENTE/ETAPA ---
        for paciente in pacientes_curso:
            etapas = Etapa.objects.filter(id_paciente=paciente).order_by('numetapa')
            etapas_stats = []
            
            for etapa in etapas:
                # 1. Porcentaje de aprobación de la etapa
                completions = EtapaCompletada.objects.filter(
                    etapa=etapa, 
                    estudiante__in=[e.estudiante for e in enrolamientos]
                ).count()
                
                perc_stage = 0
                if total_estudiantes > 0:
                    perc_stage = int((completions / total_estudiantes) * 100)
                
                # 2. Solicitudes de revisión
                req_count = SolicitudRevision.objects.filter(
                    curso=curso_activo,
                    paciente=paciente,
                    etapa_solicitud=etapa.numetapa
                ).count()
                
                etapas_stats.append({
                    'num': etapa.numetapa,
                    'nombre': etapa.nombreetapa,
                    'porcentaje': perc_stage,
                    'solicitudes': req_count
                })
            
            pacientes_global_stats.append({
                'id': paciente.id,
                'nombre': paciente.nombre,
                'etapas': etapas_stats
            })

    return render(request, 'cursosdocente/mis_cursos.html', {
        'user': docente,
        'cursos': cursos,
        'curso_activo': curso_activo,
        'estudiantes_data': estudiantes_data,
        'curso_stats': curso_stats,
        'pacientes_global_stats': pacientes_global_stats
    })

@csrf_exempt
def enrolar_estudiante(request):
    if request.method == 'POST':
        docente_id = request.session.get('usuario_id')
        curso_id = request.POST.get('curso_id')
        correo = request.POST.get('correo_estudiante')

        try:
            docente = Docente.objects.get(id=docente_id)
            curso = Curso.objects.get(id=curso_id, id_docente=docente)
            estudiante = Estudiante.objects.get(correo_institucional=correo)
            
            if Enrolamiento.objects.filter(curso=curso, estudiante=estudiante).exists():
                 return JsonResponse({'ok': False, 'error': 'El estudiante ya está inscrito en este curso.'})

            Enrolamiento.objects.create(estudiante=estudiante, curso=curso, docente=docente)
            return JsonResponse({'ok': True, 'msg': f'Estudiante {estudiante.nombre} enrolado correctamente.'})

        except Estudiante.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No existe un estudiante con ese correo.'})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

@csrf_exempt
def buscar_estudiantes_disponibles(request):
    if request.method == "GET":
        curso_id = request.GET.get("curso_id")
        term = request.GET.get("term", "").strip()

        if not curso_id:
            return JsonResponse({"ok": False, "error": "Falta ID del curso"})
       
        inscritos_ids = Enrolamiento.objects.filter(
            curso_id=curso_id
        ).values_list('estudiante_id', flat=True)

        estudiantes = Estudiante.objects.exclude(id__in=inscritos_ids)

        if term:
            estudiantes = estudiantes.filter(
                Q(nombre__icontains=term) | 
                Q(apellido__icontains=term) | 
                Q(correo_institucional__icontains=term)
            )
        
        estudiantes = estudiantes.order_by('nombre')[:20]

        data = []
        for est in estudiantes:
            data.append({
                "id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "correo": est.correo_institucional
            })

        return JsonResponse({"ok": True, "estudiantes": data})
    
    return JsonResponse({"ok": False, "error": "Método no permitido"})

@csrf_exempt
def desenrolar_estudiante(request):
    if request.method == 'POST':
        docente_id = request.session.get('usuario_id')
        curso_id = request.POST.get('curso_id')
        correo = request.POST.get('correo_estudiante')

        try:
            docente = Docente.objects.get(id=docente_id)
            curso = Curso.objects.get(id=curso_id, id_docente=docente)
            estudiante = Estudiante.objects.get(correo_institucional=correo)
            
            enrolamiento = Enrolamiento.objects.filter(curso=curso, estudiante=estudiante).first()
            
            if enrolamiento:

                SolicitudRevision.objects.filter(estudiante=estudiante, curso=curso).delete()
                
                EtapaCompletada.objects.filter(
                    estudiante=estudiante, 
                    etapa__id_paciente__id_curso=curso
                ).delete()
                
                Registro.objects.filter(
                    id_estudiante=estudiante,
                    id_pregunta__id_etapa__id_paciente__id_curso=curso
                ).delete()
                
                Registro.objects.filter(
                    id_estudiante=estudiante,
                    id_exploracion__id_etapa__id_paciente__id_curso=curso
                ).delete()
                
                enrolamiento.delete()
                
                return JsonResponse({'ok': True, 'msg': f'Estudiante {estudiante.nombre} eliminado y sus datos borrados.'})
            else:
                return JsonResponse({'ok': False, 'error': 'El estudiante no está inscrito en este curso.'})

        except (Estudiante.DoesNotExist, Curso.DoesNotExist):
            return JsonResponse({'ok': False, 'error': 'Datos inválidos.'})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def RevisionesDocenteView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login:login_docente')

    try:
        docente = Docente.objects.get(id=usuario_id)
    except Docente.DoesNotExist:
        return redirect('login:login_docente')

    solicitudes = SolicitudRevision.objects.filter(curso__id_docente=docente).order_by('-fecha_solicitud')

    curso_id = request.GET.get('curso')
    paciente_id = request.GET.get('paciente')
    etapa = request.GET.get('etapa') # 2 o 3
    estado = request.GET.get('estado') # PENDIENTE o RESPONDIDA
    estudiante_id = request.GET.get('estudiante')

    if curso_id:
        solicitudes = solicitudes.filter(curso_id=curso_id)
    if paciente_id:
        solicitudes = solicitudes.filter(paciente_id=paciente_id)
    if etapa:
        solicitudes = solicitudes.filter(etapa_solicitud=etapa)
    if estado:
        solicitudes = solicitudes.filter(estado=estado)
    if estudiante_id:
        solicitudes = solicitudes.filter(estudiante_id=estudiante_id)

    solicitudes_data = []
    for sol in solicitudes:
        respuesta_original = "No se encontró el registro."
        
        # Si es Exploración (Etapa 2)
        if sol.etapa_solicitud == 2 and sol.exploracion_especifica:
            reg = Registro.objects.filter(
                id_estudiante=sol.estudiante,
                id_exploracion=sol.exploracion_especifica
            ).first()
            if reg: respuesta_original = reg.respuesta_texto_libre
            
        # Si es Diagnóstico (Etapa 3)
        elif sol.etapa_solicitud == 3:
            # Buscamos la pregunta escrita de ese paciente
            pregunta = Pregunta.objects.filter(
                id_etapa__id_paciente=sol.paciente, 
                tipo='ESCRITA'
            ).first()
            if pregunta:
                reg = Registro.objects.filter(
                    id_estudiante=sol.estudiante,
                    id_pregunta=pregunta
                ).first()
                if reg: respuesta_original = reg.respuesta_texto_libre

        solicitudes_data.append({
            'obj': sol,
            'respuesta_original': respuesta_original
        })
        
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        respuesta_texto = request.POST.get('respuesta_texto')
        
        try:
            sol_edit = SolicitudRevision.objects.get(id=solicitud_id)
            sol_edit.respuesta_docente = respuesta_texto
            sol_edit.estado = 'RESPONDIDA'
            sol_edit.fecha_respuesta = timezone.now()
            sol_edit.save()
            return redirect('cursos:revisiones_docente') 
        except Exception as e:
            print(f"ERROR AL GUARDAR RESPUESTA: {e}")
            pass

    cursos_filter = set(s.curso for s in SolicitudRevision.objects.filter(curso__id_docente=docente))
    pacientes_filter = set(s.paciente for s in SolicitudRevision.objects.filter(curso__id_docente=docente))
    estudiantes_filter = set(s.estudiante for s in SolicitudRevision.objects.filter(curso__id_docente=docente))

    return render(request, 'cursosdocente/revisiones.html', {
        'solicitudes_data': solicitudes_data,
        'cursos_filter': cursos_filter,
        'pacientes_filter': pacientes_filter,
        'estudiantes_filter': estudiantes_filter,
        'user': docente,
        'f_curso': int(curso_id) if curso_id else '',
        'f_paciente': int(paciente_id) if paciente_id else '',
        'f_etapa': int(etapa) if etapa else '',
        'f_estado': estado or '',
        'f_estudiante': int(estudiante_id) if estudiante_id else '',
    })

def GestionCasosView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login:login_docente')
    try:
        docente = Docente.objects.get(id=usuario_id)
    except Docente.DoesNotExist:
        return redirect('login:login_docente')

    mis_cursos = Curso.objects.filter(id_docente=docente)
    mis_pacientes = Paciente.objects.filter(id_curso__id_docente=docente)

    form_curso = CursoForm()
    form_paciente = PacienteForm(user=docente)
    form_tipo_caso = TipoCasoForm()

    return render(request, 'cursosdocente/gestion_casos.html', {
        'user': docente,
        'mis_cursos': mis_cursos,
        'mis_pacientes': mis_pacientes,
        'form_curso': form_curso,
        'form_paciente': form_paciente,
        'form_tipo_caso': form_tipo_caso,
    })

# --- AJAX: Crear Curso ---
def crear_curso_ajax(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        try:
            docente = Docente.objects.get(id=usuario_id)
            form = CursoForm(request.POST)
            if form.is_valid():
                curso = form.save(commit=False)
                curso.id_docente = docente
                curso.fechacreacion = timezone.now()
                curso.save()
                return JsonResponse({'ok': True, 'msg': 'Curso creado exitosamente.'})
            else:
                return JsonResponse({'ok': False, 'error': form.errors.as_json()})
        except:
            return JsonResponse({'ok': False, 'error': 'Docente no encontrado'})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Crear Tipo Caso ---
def crear_tipo_caso_ajax(request):
    if request.method == 'POST':
        form = TipoCasoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            return JsonResponse({'ok': True, 'id': tipo.id, 'nombre': tipo.nombre})
        
        return JsonResponse({'ok': False, 'error': form.errors.as_json()})
        
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Crear Paciente ---
def crear_paciente_ajax(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        try:
            docente = Docente.objects.get(id=usuario_id)
            form = PacienteForm(docente, request.POST)
            if form.is_valid():
                form.save()
                return JsonResponse({'ok': True, 'msg': 'Paciente creado exitosamente.'})
            else:
                return JsonResponse({'ok': False, 'error': form.errors.as_json()})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Eliminar Objeto ---
def eliminar_objeto_ajax(request, modelo, pk):
    if request.method == 'POST':
        try:
            if modelo == 'curso':
                Curso.objects.get(pk=pk).delete()
            elif modelo == 'paciente':
                Paciente.objects.get(pk=pk).delete()
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Obtener datos para Editar ---
def obtener_datos_edicion(request, modelo, pk):
    data = {}
    if modelo == 'curso':
        obj = get_object_or_404(Curso, pk=pk)
        data = {'nombrecurso': obj.nombrecurso, 'objetivos': obj.objetivos}
    elif modelo == 'paciente':
        obj = get_object_or_404(Paciente, pk=pk)
        data = {
            'nombre': obj.nombre, 'edad': obj.edad, 'sexo': obj.sexo,
            'ocupacion': obj.ocupacion, 'descripcion': obj.descripcion,
            'tipo_caso': obj.tipo_caso.id, 'id_curso': obj.id_curso.id
        }
    return JsonResponse(data)

# --- AJAX: Guardar Edición ---
def guardar_edicion_ajax(request, modelo, pk):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        try:
            docente = Docente.objects.get(id=usuario_id)
            if modelo == 'curso':
                obj = get_object_or_404(Curso, pk=pk)
                form = CursoForm(request.POST, instance=obj)
            elif modelo == 'paciente':
                obj = get_object_or_404(Paciente, pk=pk)
                form = PacienteForm(docente, request.POST, instance=obj)
            
            if form.is_valid():
                form.save()
                return JsonResponse({'ok': True})
            
            return JsonResponse({'ok': False, 'error': form.errors.as_json()})
            
        except Exception as e:
             return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def ConfigurarEtapasView(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    usuario_id = request.session.get('usuario_id')
    docente = Docente.objects.get(id=usuario_id)

    # Crear etapas si no existen
    etapa1, _ = Etapa.objects.get_or_create(
        id_paciente=paciente, numetapa=1, 
        defaults={'nombreetapa': '1: Historia', 'tipo_pregunta': 'MULTIPLE'}
    )
    etapa2, _ = Etapa.objects.get_or_create(
        id_paciente=paciente, numetapa=2, 
        defaults={'nombreetapa': '2: Examen Físico', 'tipo_pregunta': 'EXPLORACIONES'}
    )
    etapa3, _ = Etapa.objects.get_or_create(
        id_paciente=paciente, numetapa=3, 
        defaults={'nombreetapa': '3: Diagnóstico', 'tipo_pregunta': 'ESCRITA'}
    )

    preguntas_e1 = Pregunta.objects.filter(id_etapa=etapa1)
    exploraciones_e2 = Exploracion.objects.filter(id_etapa=etapa2)
    diagnostico_e3 = Pregunta.objects.filter(id_etapa=etapa3, tipo='ESCRITA').first()

    # === LÓGICA DE BLOQUEO EN CADENA ===
    
    etapa1_completa = preguntas_e1.exists()
    etapa2_completa = exploraciones_e2.exists() and etapa1_completa
    etapa3_completa = bool(diagnostico_e3) and etapa2_completa

    caso_listo = etapa1_completa and etapa2_completa and etapa3_completa

    form_paciente = PacienteForm(user=docente, instance=paciente)

    context = {
        'paciente': paciente,
        'etapa1': etapa1,
        'etapa2': etapa2,
        'etapa3': etapa3,
        'preguntas_e1': preguntas_e1,
        'exploraciones_e2': exploraciones_e2,
        'diagnostico_e3': diagnostico_e3,
        'etapa1_completa': etapa1_completa,
        'etapa2_completa': etapa2_completa,
        'caso_listo': caso_listo,
        'form_paciente': form_paciente,
    }
    return render(request, 'cursosdocente/configurar_etapas.html', context)

# --- API AJAX DE GUARDADO PREGUNTA (ETAPA 1) ---
@csrf_exempt
def guardar_pregunta_etapa(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return JsonResponse({'ok': False, 'error': 'Su sesión ha expirado. Por favor, inicie sesión nuevamente.'})

        try:
            docente = Docente.objects.get(id=usuario_id)
        except Docente.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Docente no válido.'})

        try:
            with transaction.atomic():
                etapa_id = request.POST.get('etapa_id')
                pregunta_id = request.POST.get('pregunta_id')
                titulo = request.POST.get('texto_pregunta')
                video_url = request.POST.get('video_url', '')
                
                try:
                    correcta_index = int(request.POST.get('correcta_index'))
                except (ValueError, TypeError):
                    return JsonResponse({'ok': False, 'error': 'Debes seleccionar una alternativa correcta válida.'})

                if pregunta_id:
                    # === MODO EDICIÓN ===
                    preg = get_object_or_404(Pregunta, id=pregunta_id)
                    preg.titulo = titulo
                    preg.urlvideo = video_url
                    preg.save()
                    preg.opciones.all().delete() 
                else:
                    # === MODO CREACIÓN ===
                    etapa = get_object_or_404(Etapa, id=etapa_id)
                    preg = Pregunta.objects.create(
                        id_etapa=etapa,
                        docente=docente,  
                        titulo=titulo,
                        urlvideo=video_url,
                        tipo='MULTIPLE'
                    )

                for i in range(1, 5):
                    texto_op = request.POST.get(f'respuesta_{i}')
                    retro_op = request.POST.get(f'retro_{i}', '')
                    es_la_correcta = (i == correcta_index)
                    
                    if texto_op:
                        OpcionMultiple.objects.create(
                            pregunta=preg,
                            texto_opcion=texto_op,
                            retroalimentacion=retro_op,
                            is_correct=es_la_correcta
                        )

            return JsonResponse({'ok': True})
            
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def obtener_pregunta_api(request, pk):
    try:
        p = Pregunta.objects.get(pk=pk)
        opciones = p.opciones.all()
        lista = []
        for op in opciones:
            lista.append({
                'texto': op.texto_opcion,
                'retro': op.retroalimentacion,
                'es_correcta': op.is_correct
            })
        data = {'id': p.id, 'titulo': p.titulo, 'urlvideo': p.urlvideo, 'opciones': lista}
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def eliminar_pregunta_api(request, pk):
    if request.method == 'POST':
        try:
            pregunta = get_object_or_404(Pregunta, pk=pk)
            etapa = pregunta.id_etapa
            paciente = etapa.id_paciente
            
            pregunta.delete()
            
            if etapa.numetapa == 1:

                quedan_preguntas = Pregunta.objects.filter(id_etapa=etapa).exists()
                
                if not quedan_preguntas:
                    paciente.visible = False
                    paciente.completo = False
                    paciente.save()
            
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- API AJAX DE EXPLORACIÓN (ETAPA 2) ---
@csrf_exempt
def guardar_exploracion_etapa(request):
    if request.method == 'POST':
        try:
            exploracion_id = request.POST.get('exploracion_id')
            etapa_id = request.POST.get('etapa_id')
            nombre = request.POST.get('nombre_exploracion')
            instruccion = request.POST.get('indicacion_exploracion')
            retro_gral = request.POST.get('retro_exploracion')
            url_video = request.POST.get('video_url')

            if not nombre or not instruccion or not url_video:
                return JsonResponse({'ok': False, 'error': 'Faltan campos obligatorios.'})

            if exploracion_id:
                exp = get_object_or_404(Exploracion, pk=exploracion_id)
                exp.titulo = nombre
                exp.instruccion = instruccion
                exp.retroalimentacion_general = retro_gral
                exp.urlvideo = url_video
                exp.save()
            else:
                etapa = get_object_or_404(Etapa, pk=etapa_id)
                cantidad = Exploracion.objects.filter(id_etapa=etapa).count()
                if cantidad >= 6:
                     return JsonResponse({'ok': False, 'error': 'Máximo 6 exploraciones.'})
                
                Exploracion.objects.create(
                    id_etapa=etapa,
                    titulo=nombre,
                    instruccion=instruccion,
                    retroalimentacion_general=retro_gral,
                    urlvideo=url_video,
                    orden=cantidad + 1
                )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

def obtener_exploracion_api(request, pk):
    try:
        exp = get_object_or_404(Exploracion, pk=pk)
        data = {
            'id': exp.id, 'titulo': exp.titulo,
            'instruccion': exp.instruccion,
            'retroalimentacion_general': exp.retroalimentacion_general,
            'urlvideo': exp.urlvideo
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def eliminar_exploracion_api(request, pk):
    if request.method == 'POST':
        try:
            get_object_or_404(Exploracion, pk=pk).delete()
            return JsonResponse({'ok': True})
        except:
            return JsonResponse({'ok': False})
    return JsonResponse({'ok': False})

# --- API AJAX DE DIAGNÓSTICO (ETAPA 3) ---
@csrf_exempt
def guardar_diagnostico_etapa(request):
    if request.method == 'POST':
        try:
            pregunta_id = request.POST.get('pregunta_id')
            etapa_id = request.POST.get('etapa_id')
            titulo = request.POST.get('titulo_diagnostico')
            retro = request.POST.get('retro_diagnostico')
            url_video = request.POST.get('video_url', '')

            if not titulo:
                return JsonResponse({'ok': False, 'error': 'Falta el título.'})

            usuario_id = request.session.get('usuario_id')
            docente = Docente.objects.get(id=usuario_id)

            if pregunta_id:
                preg = get_object_or_404(Pregunta, pk=pregunta_id)
                preg.titulo = titulo
                preg.retroalimentacion_general = retro
                preg.urlvideo = url_video
                preg.save()
            else:
                etapa = get_object_or_404(Etapa, pk=etapa_id)
                if Pregunta.objects.filter(id_etapa=etapa).exists():
                     return JsonResponse({'ok': False, 'error': 'Ya existe diagnóstico.'})

                Pregunta.objects.create(
                    id_etapa=etapa,
                    titulo=titulo,
                    tipo='ESCRITA',
                    docente=docente,
                    clave_respuesta_escrita="",
                    retroalimentacion_general=retro,
                    urlvideo=url_video
                )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

def obtener_diagnostico_api(request, pk):
    try:
        preg = get_object_or_404(Pregunta, pk=pk)
        data = {
            'id': preg.id, 'titulo': preg.titulo,
            'retroalimentacion_general': preg.retroalimentacion_general,
            'urlvideo': preg.urlvideo
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def eliminar_diagnostico_api(request, pk):
    if request.method == 'POST':
        try:
            get_object_or_404(Pregunta, pk=pk).delete()
            return JsonResponse({'ok': True})
        except:
            return JsonResponse({'ok': False})
    return JsonResponse({'ok': False})

@csrf_exempt
def toggle_visibilidad_paciente(request, pk):
    if request.method == 'POST':
        try:
            paciente = Paciente.objects.get(pk=pk)
            if not paciente.visible:
                e1 = Etapa.objects.filter(id_paciente=paciente, numetapa=1).first()
                e2 = Etapa.objects.filter(id_paciente=paciente, numetapa=2).first()
                e3 = Etapa.objects.filter(id_paciente=paciente, numetapa=3).first()
                
                has_q1 = Pregunta.objects.filter(id_etapa=e1).exists() if e1 else False
                has_ex2 = Exploracion.objects.filter(id_etapa=e2).exists() if e2 else False
                has_diag3 = Pregunta.objects.filter(id_etapa=e3, tipo='ESCRITA').exists() if e3 else False

                if not (has_q1 and has_ex2 and has_diag3):
                    return JsonResponse({'ok': False, 'error': 'Caso incompleto.'})

            paciente.visible = not paciente.visible
            paciente.save()
            return JsonResponse({'ok': True, 'estado': paciente.visible})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

@csrf_exempt
def eliminar_registros_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            paciente_id = data.get('paciente_id')
            tipo = data.get('tipo')
            
            if tipo == 'unico':
                correo = data.get('estudiante')
                estudiante = Estudiante.objects.get(correo_institucional=correo)
                
                Registro.objects.filter(id_estudiante=estudiante, id_pregunta__id_etapa__id_paciente_id=paciente_id).delete()
                Registro.objects.filter(id_estudiante=estudiante, id_exploracion__id_etapa__id_paciente_id=paciente_id).delete()
                EtapaCompletada.objects.filter(estudiante=estudiante, etapa__id_paciente_id=paciente_id).delete()
                SolicitudRevision.objects.filter(estudiante=estudiante, paciente__id=paciente_id).delete()
            
            elif tipo == 'todos':
                Registro.objects.filter(id_pregunta__id_etapa__id_paciente_id=paciente_id).delete()
                Registro.objects.filter(id_exploracion__id_etapa__id_paciente_id=paciente_id).delete()
                EtapaCompletada.objects.filter(etapa__id_paciente_id=paciente_id).delete()
                SolicitudRevision.objects.filter(paciente__id=paciente_id).delete()
            
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

# ====================================================
# === NUEVA VISTA: DETALLE INTENTOS POR ESTUDIANTE ===
# ====================================================
def obtener_detalle_intentos(request, estudiante_id, etapa_id):
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    registros = Registro.objects.filter(
        id_estudiante=estudiante_id,
        id_pregunta__id_etapa=etapa_id
    ).select_related('id_pregunta')

    detalles = []
    
    for reg in registros:
        puntaje = max(0, 3 - reg.intentos_fallidos)
        detalles.append({
            "pregunta": reg.id_pregunta.titulo,
            "errores": reg.intentos_fallidos,
            "puntaje": puntaje
        })

    return JsonResponse({"ok": True, "detalles": detalles})