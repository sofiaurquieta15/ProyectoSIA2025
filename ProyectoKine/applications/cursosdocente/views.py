import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Count
from .forms import CursoForm, PacienteForm, TipoCasoForm
from django.utils import timezone
from django.core.exceptions import ValidationError
from applications.casospacientes.models import Etapa, Exploracion
# Modelos
from applications.login.models import Docente, Estudiante
from .models import Curso
# IMPORTANTE: Agregamos SolicitudRevision a los imports
from applications.cursosestudiante.models import Enrolamiento, SolicitudRevision
from applications.casospacientes.models import Paciente, TipoCaso, Etapa, EtapaCompletada, Registro, Pregunta, Exploracion, OpcionMultiple

def MenuDocenteView(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login:login_docente')
    try: usuario = Docente.objects.get(id=usuario_id)
    except Docente.DoesNotExist: return redirect('login:login_docente')
    return render(request, 'cursosdocente/menudocente.html', {'user': usuario})


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

        pacientes_curso = Paciente.objects.filter(id_curso=curso_activo)
        
        # --- A. PROCESAR DATOS DE CADA ESTUDIANTE ---
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
                        'num': etapa.numetapa,
                        'nombre': etapa.nombreetapa,
                        'completada': hecha
                    })
                    
                    total_etapas += 1
                    if hecha: etapas_completadas += 1
                
                pacientes_info.append({
                    'nombre': paciente.nombre,
                    'etapas': etapas_info_p
                })
            
            porcentaje = 0
            if total_etapas > 0:
                porcentaje = int((etapas_completadas / total_etapas) * 100)
            
            # Contar para el global si el alumno terminó todo (100%)
            if porcentaje == 100:
                curso_stats['completados'] += 1

            estudiantes_data.append({
                'obj': est,
                'porcentaje': porcentaje,
                'pacientes': pacientes_info, # Lista Python pura (se convierte con filtro en template)
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
                # 1. Porcentaje de aprobación de la etapa (cuántos alumnos la hicieron)
                completions = EtapaCompletada.objects.filter(
                    etapa=etapa, 
                    estudiante__in=[e.estudiante for e in enrolamientos]
                ).count()
                
                perc_stage = 0
                if total_estudiantes > 0:
                    perc_stage = int((completions / total_estudiantes) * 100)
                
                # 2. Solicitudes de revisión enviadas para esta etapa
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
        'curso_stats': curso_stats, # Nueva Data
        'pacientes_global_stats': pacientes_global_stats # Nueva Data
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
                # --- LIMPIEZA PROFUNDA DE DATOS ---
                
                # 1. Borrar Solicitudes de Revisión en este curso
                SolicitudRevision.objects.filter(estudiante=estudiante, curso=curso).delete()
                
                # 2. Borrar Etapas Completadas (Avance) de pacientes de este curso
                EtapaCompletada.objects.filter(
                    estudiante=estudiante, 
                    etapa__id_paciente__id_curso=curso
                ).delete()
                
                # 3. Borrar Registros (Respuestas Preguntas) de este curso
                # Usamos la relación: Registro -> Pregunta -> Etapa -> Paciente -> Curso
                Registro.objects.filter(
                    id_estudiante=estudiante,
                    id_pregunta__id_etapa__id_paciente__id_curso=curso
                ).delete()
                
                # 4. Borrar Registros (Respuestas Exploraciones) de este curso
                Registro.objects.filter(
                    id_estudiante=estudiante,
                    id_exploracion__id_etapa__id_paciente__id_curso=curso
                ).delete()
                
                # 5. Finalmente, eliminar el enrolamiento
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

    # 1. Obtener todas las solicitudes de LOS CURSOS de este docente
    solicitudes = SolicitudRevision.objects.filter(curso__id_docente=docente).order_by('-fecha_solicitud')

    # 2. Filtros
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

    # 3. Enriquecer datos (Buscar la respuesta original del estudiante)
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

    # 4. Procesar Respuesta del Docente (POST)
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        respuesta_texto = request.POST.get('respuesta_texto')
        
        try:
            sol_edit = SolicitudRevision.objects.get(id=solicitud_id)
            sol_edit.respuesta_docente = respuesta_texto
            sol_edit.estado = 'RESPONDIDA'
            sol_edit.fecha_respuesta = timezone.now()
            sol_edit.save()
            return redirect('cursos:revisiones_docente') # Recargar para ver cambios
        except:
            pass

    # Listas para los filtros (Dropdowns)
    # Usamos set() para valores únicos
    cursos_filter = set(s.curso for s in SolicitudRevision.objects.filter(curso__id_docente=docente))
    pacientes_filter = set(s.paciente for s in SolicitudRevision.objects.filter(curso__id_docente=docente))
    estudiantes_filter = set(s.estudiante for s in SolicitudRevision.objects.filter(curso__id_docente=docente))

    return render(request, 'cursosdocente/revisiones.html', {
        'solicitudes_data': solicitudes_data,
        'cursos_filter': cursos_filter,
        'pacientes_filter': pacientes_filter,
        'estudiantes_filter': estudiantes_filter,
        'user': docente,
        # Preservar filtros
        'f_curso': int(curso_id) if curso_id else '',
        'f_paciente': int(paciente_id) if paciente_id else '',
        'f_etapa': int(etapa) if etapa else '',
        'f_estado': estado or '',
        'f_estudiante': int(estudiante_id) if estudiante_id else '',
    })

def GestionCasosView(request):
    # Validar sesión docente
    usuario_id = request.session.get('usuario_id')
    if not usuario_id or request.session.get('rol') != 'Docente':
        return redirect('login:login_docente')
    
    docente = Docente.objects.get(id=usuario_id)

    # Listados para la pestaña "GESTIÓN/EDITAR"
    mis_cursos = Curso.objects.filter(id_docente=docente)
    # Pacientes asociados a los cursos de este docente
    mis_pacientes = Paciente.objects.filter(id_curso__id_docente=docente)

    # Formularios vacíos para los modales de creación
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
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Crear Tipo Caso (Popup) ---
def crear_tipo_caso_ajax(request):
    if request.method == 'POST':
        form = TipoCasoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            return JsonResponse({'ok': True, 'id': tipo.id, 'nombre': tipo.nombre})
        return JsonResponse({'ok': False, 'error': 'Error al crear tipo.'})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# --- AJAX: Crear Paciente ---
def crear_paciente_ajax(request):
    if request.method == 'POST':
        usuario_id = request.session.get('usuario_id')
        docente = Docente.objects.get(id=usuario_id)
        form = PacienteForm(docente, request.POST) # Pasamos el docente para filtrar cursos
        if form.is_valid():
            form.save()
            return JsonResponse({'ok': True, 'msg': 'Paciente creado exitosamente.'})
        else:
            return JsonResponse({'ok': False, 'error': str(form.errors)})
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
        if modelo == 'curso':
            obj = get_object_or_404(Curso, pk=pk)
            form = CursoForm(request.POST, instance=obj)
        elif modelo == 'paciente':
            usuario_id = request.session.get('usuario_id')
            docente = Docente.objects.get(id=usuario_id)
            obj = get_object_or_404(Paciente, pk=pk)
            form = PacienteForm(docente, request.POST, instance=obj)
        
        if form.is_valid():
            form.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': str(form.errors)})
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

def ConfigurarEtapasView(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    
    # Obtener el docente para inicializar el formulario correctamente (filtrar cursos)
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

    # Contenido existente
    preguntas_e1 = Pregunta.objects.filter(id_etapa=etapa1)
    exploraciones_e2 = Exploracion.objects.filter(id_etapa=etapa2)
    diagnostico_e3 = Pregunta.objects.filter(id_etapa=etapa3, tipo='ESCRITA').first()

    # Validación de Progreso
    etapa1_completa = preguntas_e1.exists()
    etapa2_completa = exploraciones_e2.exists()
    etapa3_completa = bool(diagnostico_e3)
    caso_listo = etapa1_completa and etapa2_completa and etapa3_completa

    # NUEVO: Formulario para editar paciente (Pre-llenado con instance=paciente)
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
        'form_paciente': form_paciente, # <--- Enviamos el form al template
    }
    
    return render(request, 'cursosdocente/configurar_etapas.html', context)

# --- APIs AJAX DE GUARDADO ---

@csrf_exempt
def guardar_pregunta_etapa(request):
    if request.method == 'POST':
        try:
            etapa_id = request.POST.get('etapa_id')
            texto_titulo = request.POST.get('texto_pregunta')
            video_url = request.POST.get('video_url')
            
            docente_id = request.session.get('usuario_id')
            docente = Docente.objects.get(id=docente_id)
            etapa = Etapa.objects.get(id=etapa_id)
            
            # CORRECCIÓN: Eliminamos el campo 'texto' que ya no existe en tu modelo
            pregunta = Pregunta.objects.create(
                id_etapa=etapa, 
                titulo=texto_titulo, 
                # texto="Seleccione la alternativa correcta",  <-- ELIMINADO
                tipo='MULTIPLE',
                docente=docente,
                urlvideo=video_url
            )
            
            # Guardar 4 Respuestas
            correcta_idx = int(request.POST.get('correcta_index'))
            
            for i in range(1, 5):
                texto_resp = request.POST.get(f'respuesta_{i}')
                texto_retro = request.POST.get(f'retro_{i}', '') # Valor por defecto vacío
                es_correcta = (i == correcta_idx)
                
                OpcionMultiple.objects.create(
                    pregunta=pregunta, 
                    texto_opcion=texto_resp, 
                    is_correct=es_correcta,
                    retroalimentacion=texto_retro
                )
                
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

@csrf_exempt
def guardar_exploracion_etapa(request):
    if request.method == 'POST':
        try:
            etapa_id = request.POST.get('etapa_id')
            exploracion_id = request.POST.get('exploracion_id')
            nombre = request.POST.get('nombre_exploracion')
            indicacion = request.POST.get('indicacion_exploracion')
            retro = request.POST.get('retro_exploracion')
            video_url = request.POST.get('video_url') # Nuevo campo
            
            etapa = Etapa.objects.get(id=etapa_id)
            
            if exploracion_id:
                exploracion = get_object_or_404(Exploracion, id=exploracion_id)

                exploracion.titulo = nombre
                exploracion.instruccion = indicacion
                exploracion.retroalimentacion_general = retro
                exploracion.urlvideo = video_url
            else:
                cantidad_actual = Exploracion.objects.filter(id_etapa=etapa).count()
                if cantidad_actual >= 6:
                    return JsonResponse({
                        'ok':False,
                        'error': 'Limite alcanzado: Máximo de 6 exploraciones permitidas por etapa'
                    }, status=400)

                orden_actual = cantidad_actual + 1

                exploracion = Exploracion(
                    id_etapa=etapa,
                    titulo=nombre,
                    instruccion=indicacion,
                    retroalimentacion_general=retro,
                    orden=orden_actual,
                    urlvideo=video_url
                )
            
            exploracion.save()

            return JsonResponse({'ok':True, 'id':exploracion.id})
        
        except ValidationError as e:
            return JsonResponse({'ok': False, 'error':e.nessages[0]})
           
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False})

@csrf_exempt
def guardar_diagnostico_etapa(request):
    if request.method == 'POST':
        try:
            etapa_id = request.POST.get('etapa_id')
            diagnostico_texto = request.POST.get('diagnostico')
            video_url = request.POST.get('video_url') # Nuevo campo
            
            docente_id = request.session.get('usuario_id')
            docente = Docente.objects.get(id=docente_id)
            etapa = Etapa.objects.get(id=etapa_id)
            
            # Guardamos/Actualizamos la pregunta de diagnóstico
            pregunta, created = Pregunta.objects.update_or_create(
                id_etapa=etapa,
                tipo='ESCRITA',
                defaults={
                    'titulo': 'Diagnóstico Final',
                    'texto': 'Realice el diagnóstico correspondiente al caso',
                    'docente': docente,
                    'clave_respuesta_escrita': diagnostico_texto,
                    'urlvideo': video_url # Asociamos el video aquí
                }
            )
            
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False})

@csrf_exempt
def eliminar_pregunta_api(request, pk):
    if request.method == 'POST':
        try:
            Pregunta.objects.get(pk=pk).delete()
            return JsonResponse({'ok': True})
        except:
            return JsonResponse({'ok': False})
    return JsonResponse({'ok': False})

def obtener_pregunta_api(request, pk):
    try:
        p = Pregunta.objects.get(pk=pk)
        opciones = p.opciones.all() # Asegúrate que related_name='opciones' en tu modelo OpcionMultiple
        
        lista_opciones = []
        for op in opciones:
            lista_opciones.append({
                'texto': op.texto_opcion,
                'retro': op.retroalimentacion,
                'es_correcta': op.is_correct
            })
            
        data = {
            'id': p.id,
            'titulo': p.titulo,
            'urlvideo': p.urlvideo,
            'opciones': lista_opciones
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Y ACTUALIZAR guardar_pregunta_etapa PARA SOPORTAR EDICIÓN (ID existente)
@csrf_exempt
def guardar_pregunta_etapa(request):
    if request.method == 'POST':
        try:
            pregunta_id = request.POST.get('pregunta_id') # ID si es edición
            etapa_id = request.POST.get('etapa_id')
            texto_titulo = request.POST.get('texto_pregunta')
            video_url = request.POST.get('video_url')
            
            if pregunta_id:
                # EDICIÓN
                pregunta = Pregunta.objects.get(pk=pregunta_id)
                pregunta.titulo = texto_titulo
                pregunta.urlvideo = video_url
                pregunta.save()
                
                # Borramos opciones viejas y creamos nuevas (más fácil que editar una por una)
                pregunta.opciones.all().delete()
            else:
                # CREACIÓN
                etapa = Etapa.objects.get(id=etapa_id)
                docente = Docente.objects.get(id=request.session.get('usuario_id'))
                pregunta = Pregunta.objects.create(
                    id_etapa=etapa, 
                    titulo=texto_titulo, 
                    tipo='MULTIPLE',
                    docente=docente,
                    urlvideo=video_url
                )
            
            # Guardar Opciones (Igual para ambos casos)
            correcta_idx = int(request.POST.get('correcta_index'))
            for i in range(1, 5):
                texto_resp = request.POST.get(f'respuesta_{i}')
                texto_retro = request.POST.get(f'retro_{i}', '')
                OpcionMultiple.objects.create(
                    pregunta=pregunta, 
                    texto_opcion=texto_resp, 
                    is_correct=(i == correcta_idx),
                    retroalimentacion=texto_retro
                )
                
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

# 1. ACTUALIZAR: Guardar / Editar Exploración
@csrf_exempt
def guardar_exploracion_etapa(request):
    if request.method == 'POST':
        try:
            # Recibir datos
            exploracion_id = request.POST.get('exploracion_id')
            etapa_id = request.POST.get('etapa_id')
            nombre = request.POST.get('nombre_exploracion')
            instruccion = request.POST.get('indicacion_exploracion')
            retro_gral = request.POST.get('retro_exploracion') # Campo nuevo
            url_video = request.POST.get('video_url') # Obligatorio

            # Validaciones básicas
            if not nombre or not instruccion or not url_video:
                return JsonResponse({'ok': False, 'error': 'Faltan campos obligatorios (Nombre, Instrucción o Video).'})

            if exploracion_id:
                # --- EDICIÓN ---
                exp = get_object_or_404(Exploracion, pk=exploracion_id)
                exp.titulo = nombre
                exp.instruccion = instruccion
                exp.retroalimentacion_general = retro_gral
                exp.urlvideo = url_video
                exp.save() # El método save() del modelo se encarga de convertir a embed
            else:
                # --- CREACIÓN ---
                etapa = get_object_or_404(Etapa, pk=etapa_id)
                # Calcular orden
                orden_actual = Exploracion.objects.filter(id_etapa=etapa).count() + 1
                
                Exploracion.objects.create(
                    id_etapa=etapa,
                    titulo=nombre,
                    instruccion=instruccion,
                    retroalimentacion_general=retro_gral,
                    urlvideo=url_video,
                    orden=orden_actual
                )
            
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# 2. OBTENER (Para editar)
def obtener_exploracion_api(request, pk):
    try:
        exp = get_object_or_404(Exploracion, pk=pk)
        data = {
            'id': exp.id,
            'titulo': exp.titulo,
            'instruccion': exp.instruccion,
            'retroalimentacion_general': exp.retroalimentacion_general,
            'urlvideo': exp.urlvideo
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# 3. ELIMINAR
@csrf_exempt
def eliminar_exploracion_api(request, pk):
    if request.method == 'POST':
        try:
            exp = get_object_or_404(Exploracion, pk=pk)
            exp.delete()
            # Opcional: Reordenar las exploraciones restantes aquí si fuera necesario
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

# 1. GUARDAR DIAGNÓSTICO (Etapa 3)
@csrf_exempt
def guardar_diagnostico_etapa(request):
    if request.method == 'POST':
        try:
            # 1. Obtener datos del formulario
            pregunta_id = request.POST.get('pregunta_id')
            etapa_id = request.POST.get('etapa_id')
            titulo = request.POST.get('titulo_diagnostico')
            retro = request.POST.get('retro_diagnostico')
            url_video = request.POST.get('video_url', '')

            # 2. VALIDACIÓN BÁSICA
            if not titulo:
                return JsonResponse({'ok': False, 'error': 'Falta el título de la pregunta de diagnóstico.'})

            # 3. RECUPERAR AL DOCENTE (CRUCIAL PARA EL ERROR)
            usuario_id = request.session.get('usuario_id')
            docente = Docente.objects.get(id=usuario_id)

            if pregunta_id:
                # --- CASO EDITAR ---
                preg = get_object_or_404(Pregunta, pk=pregunta_id)
                preg.titulo = titulo
                preg.retroalimentacion_general = retro
                preg.urlvideo = url_video
                # Nota: No cambiamos el docente al editar, mantenemos el creador original
                preg.save()
            else:
                # --- CASO CREAR ---
                etapa = get_object_or_404(Etapa, pk=etapa_id)
                
                # Verificar duplicados
                if Pregunta.objects.filter(id_etapa=etapa).exists():
                     return JsonResponse({'ok': False, 'error': 'Ya existe un diagnóstico para este paciente.'})

                Pregunta.objects.create(
                    id_etapa=etapa,
                    titulo=titulo,
                    tipo='ESCRITA',
                    docente=docente,            # <--- AQUÍ ESTABA EL ERROR (Faltaba esta línea)
                    clave_respuesta_escrita="", # Guardamos vacío para cumplir requisitos si los hay
                    retroalimentacion_general=retro,
                    urlvideo=url_video
                )
            
            return JsonResponse({'ok': True})
        except Exception as e:
            print(f"Error en guardar_diagnostico: {e}") # Log para depuración
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'})

# 2. OBTENER (Para editar)
def obtener_diagnostico_api(request, pk):
    try:
        preg = get_object_or_404(Pregunta, pk=pk)
        data = {
            'id': preg.id,
            'titulo': preg.titulo,
            'clave_respuesta_escrita': preg.clave_respuesta_escrita, # La respuesta correcta
            'retroalimentacion_general': preg.retroalimentacion_general,
            'urlvideo': preg.urlvideo
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# 3. ELIMINAR
@csrf_exempt
def eliminar_diagnostico_api(request, pk):
    if request.method == 'POST':
        try:
            preg = get_object_or_404(Pregunta, pk=pk)
            preg.delete()
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
    return JsonResponse({'ok': False})

@csrf_exempt
def toggle_visibilidad_paciente(request, pk):
    if request.method == 'POST':
        try:
            paciente = Paciente.objects.get(pk=pk)
            
            # Validar integridad antes de permitir mostrar
            # (Doble chequeo de seguridad por si alguien fuerza la petición)
            if not paciente.visible: # Si quiere mostrarlo
                # Verificar que tenga las 3 etapas con contenido
                e1 = Etapa.objects.filter(id_paciente=paciente, numetapa=1).first()
                e2 = Etapa.objects.filter(id_paciente=paciente, numetapa=2).first()
                e3 = Etapa.objects.filter(id_paciente=paciente, numetapa=3).first()
                
                has_q1 = Pregunta.objects.filter(id_etapa=e1).exists() if e1 else False
                has_ex2 = Exploracion.objects.filter(id_etapa=e2).exists() if e2 else False
                has_diag3 = Pregunta.objects.filter(id_etapa=e3, tipo='ESCRITA').exists() if e3 else False

                if not (has_q1 and has_ex2 and has_diag3):
                    return JsonResponse({'ok': False, 'error': 'El caso está incompleto. No se puede publicar.'})

            # Cambiar estado
            paciente.visible = not paciente.visible
            paciente.save()
            
            estado_txt = "VISIBLE" if paciente.visible else "OCULTO"
            return JsonResponse({'ok': True, 'estado': paciente.visible, 'msg': f'Paciente ahora está {estado_txt}'})
            
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False})

@csrf_exempt
def eliminar_registros_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            paciente_id = data.get('paciente_id')
            tipo = data.get('tipo') # 'unico' o 'todos'
            
            if tipo == 'unico':
                correo = data.get('estudiante')
                try:
                    estudiante = Estudiante.objects.get(correo_institucional=correo)
                    
                    # 1. Borrar Registros (Respuestas de Etapas)
                    Registro.objects.filter(
                        id_estudiante=estudiante,
                        id_pregunta__id_etapa__id_paciente_id=paciente_id
                    ).delete()
                    
                    Registro.objects.filter(
                        id_estudiante=estudiante,
                        id_exploracion__id_etapa__id_paciente_id=paciente_id
                    ).delete()
                    
                    # 2. Borrar Avance (Etapas Completadas)
                    EtapaCompletada.objects.filter(
                        estudiante=estudiante,
                        etapa__id_paciente_id=paciente_id
                    ).delete()

                    # 3. --- NUEVO: Borrar Solicitudes de Revisión ---
                    SolicitudRevision.objects.filter(
                        estudiante=estudiante,
                        paciente__id=paciente_id
                    ).delete()
                    
                except Estudiante.DoesNotExist:
                    return JsonResponse({'ok': False, 'error': 'Estudiante no encontrado'})
            
            elif tipo == 'todos':
                # 1. Borrar TODOS los Registros
                Registro.objects.filter(id_pregunta__id_etapa__id_paciente_id=paciente_id).delete()
                Registro.objects.filter(id_exploracion__id_etapa__id_paciente_id=paciente_id).delete()
                
                # 2. Borrar TODOS los Avances
                EtapaCompletada.objects.filter(etapa__id_paciente_id=paciente_id).delete()

                # 3. --- NUEVO: Borrar TODAS las Solicitudes ---
                SolicitudRevision.objects.filter(paciente__id=paciente_id).delete()
            
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})
            
    return JsonResponse({'ok': False})