import json
from django.views.generic import ListView, TemplateView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from applications.cursosdocente.models import Curso
from applications.login.models import Estudiante
from .models import (
    Paciente,
    Etapa,
    Pregunta,
    OpcionMultiple,
    Exploracion,
    Registro,
    EtapaCompletada
)

# ============================================================
# ===============  LISTA PACIENTES POR CURSO  =================
# ============================================================

class ListaPacientesPorCursoView(ListView):
    model = Paciente
    template_name = 'casospacientes/lista_casos.html'
    context_object_name = 'pacientes_raw'

    def get_queryset(self):
        id_curso = self.kwargs['id_curso']
        return Paciente.objects.filter(id_curso=id_curso)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_curso = self.kwargs['id_curso']
        curso = Curso.objects.get(id=id_curso)

        # Obtener estudiante de la sesión
        estudiante_id = self.request.session.get("estudiante_id")
        estudiante = Estudiante.objects.get(id=estudiante_id)

        pacientes = context["pacientes_raw"]

        pacientes_data = []

        for p in pacientes:
            # Total de etapas del caso
            total_etapas = Etapa.objects.filter(id_paciente=p).count()

            # Etapas que el estudiante tiene completadas
            etapas_completadas = EtapaCompletada.objects.filter(
                estudiante=estudiante,
                etapa__id_paciente=p
            ).count()

            pacientes_data.append({
                "paciente": p,
                "completado": (total_etapas == etapas_completadas),
            })

        # Reemplazar en el template
        context["curso"] = curso
        context["pacientes_data"] = pacientes_data

        return context

# ============================================================
# ===================== DETALLE PACIENTE ======================
# ============================================================

class DetallePacienteView(TemplateView):
    template_name = 'casospacientes/detalle_paciente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paciente = Paciente.objects.get(id=self.kwargs['id_paciente'])
        etapas = Etapa.objects.filter(id_paciente=paciente).order_by('numetapa')

        estudiante_id = self.request.session.get("estudiante_id")
        estudiante = Estudiante.objects.get(id=estudiante_id)

        completadas = EtapaCompletada.objects.filter(
            estudiante=estudiante,
            etapa__in=etapas
        ).values_list("etapa_id", flat=True)

        etapas_con_estado = []
        desbloquear = True

        for e in etapas:
            estado = {
                "obj": e,
                "completada": (e.id in completadas),
                "bloqueada": not desbloquear
            }

            if not estado["completada"]:
                desbloquear = False

            etapas_con_estado.append(estado)

        context.update({
            "paciente": paciente,
            "etapas": etapas_con_estado
        })

        return context


# ============================================================
# ======================== VISTA ETAPA ========================
# ============================================================

class VistaEtapaView(TemplateView):
    template_name = 'casospacientes/etapa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_paciente = kwargs["id_paciente"]
        numetapa = kwargs["numetapa"]

        etapa = get_object_or_404(
            Etapa,
            id_paciente=id_paciente,
            numetapa=numetapa
        )

        tipo = etapa.tipo_pregunta
        paciente = etapa.id_paciente

        total_etapas = Etapa.objects.filter(id_paciente=paciente).count()

        estudiante_id = self.request.session.get("estudiante_id")
        estudiante = Estudiante.objects.get(id=estudiante_id)

        completada = EtapaCompletada.objects.filter(
            estudiante=estudiante,
            etapa=etapa
        ).exists()

        context.update({
            "num_etapa": numetapa,
            "etapa": etapa,
            "tipo": tipo,
            "ultima_etapa": (numetapa == total_etapas),
            "completada": completada,
            "paciente": paciente
        })

        # ETAPA 1 — MULTIPLE CHOICE
        if tipo == "MULTIPLE":
            preguntas = Pregunta.objects.filter(id_etapa=etapa).prefetch_related("opciones")

            respuestas_previas = {
                r.id_pregunta.id: r.opcion_seleccionada.id
                for r in Registro.objects.filter(
                    id_estudiante=estudiante,
                    id_pregunta__in=preguntas
                )
                if r.opcion_seleccionada
            }

            context.update({
                "preguntas": preguntas,
                "respuestas_previas": respuestas_previas
            })

        # ETAPA 3 — RESPUESTA ESCRITA
        elif tipo == "ESCRITA":
            pregunta = Pregunta.objects.get(id_etapa=etapa)

            registro = Registro.objects.filter(
                id_pregunta=pregunta,
                id_estudiante=estudiante
            ).first()

            context.update({
                "pregunta": pregunta,
                "respuesta_previa": registro.respuesta_texto_libre if registro else ""
            })

        return context

class VistaEtapa2View(TemplateView):
    template_name = "casospacientes/etapa2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_paciente = kwargs["id_paciente"]
        numetapa = kwargs["numetapa"]

        etapa = get_object_or_404(
            Etapa,
            id_paciente=id_paciente,
            numetapa=numetapa
        )

        exploraciones = etapa.exploraciones.order_by("orden")
        paciente = etapa.id_paciente

        estudiante_id = self.request.session.get("estudiante_id")
        estudiante = Estudiante.objects.get(id=estudiante_id)

        # Respuestas ya registradas
        registros = Registro.objects.filter(
            id_estudiante=estudiante,
            id_exploracion__in=exploraciones
        )

        respuestas_dict = {
            r.id_exploracion.id: r.respuesta_texto_libre
            for r in registros
        }

        # Retroalimentación general por exploración
        retro_dict = {
            exp.id: (exp.retroalimentacion_general or "")
            for exp in exploraciones
        }

        total_etapas = Etapa.objects.filter(id_paciente=paciente).count()

        completada = EtapaCompletada.objects.filter(
            estudiante=estudiante,
            etapa=etapa
        ).exists()

        context.update({
            "etapa": etapa,
            "exploraciones": exploraciones,
            "paciente": paciente,
            "num_etapa": numetapa,
            "ultima_etapa": (numetapa == total_etapas),
            "completada": completada,
            "respuestas_estudiante_json": json.dumps(respuestas_dict),
            "retro_exploraciones_json": json.dumps(retro_dict),
        })

        return context

class VistaEtapa3View(TemplateView):
    template_name = "casospacientes/etapa3.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_paciente = kwargs["id_paciente"]
        numetapa = kwargs["numetapa"]

        # Obtener etapa 3
        etapa = get_object_or_404(
            Etapa,
            id_paciente=id_paciente,
            numetapa=numetapa
        )

        # Obtener la única pregunta asociada a esta etapa
        pregunta = Pregunta.objects.filter(id_etapa=etapa).first()

        # Estudiante actual
        estudiante_id = self.request.session.get("estudiante_id")
        estudiante = Estudiante.objects.get(id=estudiante_id)

        # Buscar respuesta del estudiante (si existe)
        registro = Registro.objects.filter(
            id_pregunta=pregunta,
            id_estudiante=estudiante
        ).first()

        completada = registro is not None

        paciente = etapa.id_paciente
        total_etapas = Etapa.objects.filter(id_paciente=paciente).count()

        context.update({
            "etapa": etapa,
            "pregunta": pregunta,
            "paciente": paciente,
            "num_etapa": numetapa,
            "ultima_etapa": (numetapa == total_etapas),
            "completada": completada,
            "respuesta": registro.respuesta_texto_libre if registro else "",
        })

        return context


# ============================================================
# ========================= AJAX ==============================
# ============================================================

@csrf_exempt
def validar_respuesta_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    # 1. Leer JSON
    try:
        data = json.loads(request.body)
        estudiante_id = data.get("estudiante_id")
        
        # Datos Etapa 1 (Lista de opciones)
        respuestas_cliente = data.get("respuestas", [])
        
        # Datos Etapa 3 (Texto directo)
        texto_respuesta_global = data.get("texto_respuesta", "").strip()
        pregunta_id_global = data.get("pregunta_id")

    except Exception as e:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # 2. Validar estudiante
    if not estudiante_id:
        return JsonResponse({"error": "Falta estudiante_id"}, status=400)
    
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return JsonResponse({"error": "Estudiante no encontrado"}, status=404)

    # ============================================================
    # CASO A: ETAPA 3 (RESPUESTA ESCRITA)
    # Detectamos si viene texto_respuesta y pregunta_id
    # ============================================================
    if texto_respuesta_global and pregunta_id_global:
        try:
            pregunta = Pregunta.objects.get(id=pregunta_id_global)
            etapa = pregunta.id_etapa
        except Pregunta.DoesNotExist:
            return JsonResponse({"error": "Pregunta no encontrada"}, status=404)

        # Guardar respuesta (update_or_create para evitar duplicados si reenvía)
        registro, creado = Registro.objects.update_or_create(
            id_pregunta=pregunta,
            id_estudiante=estudiante,
            defaults={
                "respuesta_texto_libre": texto_respuesta_global,
                "calificacion_obtenida": None  # Pendiente de revisión docente si aplica
            }
        )

        # Marcar etapa completada automáticamente al enviar
        EtapaCompletada.objects.get_or_create(
            estudiante=estudiante,
            etapa=etapa
        )

        return JsonResponse({
            "ok": True,
            "retro": pregunta.retroalimentacion_general or "Diagnóstico registrado exitosamente.",
            "msg": "Respuesta guardada."
        })

    # ============================================================
    # CASO B: ETAPA 1 (SELECCIÓN MÚLTIPLE)
    # Procesamos la lista de respuestas
    # ============================================================
    
    errores = []
    correctas_objs = []
    etapa_actual = None

    for item in respuestas_cliente:
        p_id = item.get("pregunta_id")
        op_id = item.get("opcion_id")
        
        # Si falta la opción, saltamos (esto evita que el código de Etapa 1 trate de procesar datos de Etapa 3)
        if not op_id: 
            continue

        try:
            pregunta = Pregunta.objects.get(id=p_id)
            opcion = OpcionMultiple.objects.get(id=op_id)
            
            if not opcion.is_correct:
                errores.append({
                    "pregunta_id": p_id,
                    "titulo_pregunta": pregunta.titulo,
                    "opcion_texto": opcion.texto_opcion,
                    "opcion_id": op_id,
                    "retro": opcion.retroalimentacion or "Incorrecto. Intenta de nuevo."
                })
            else:
                correctas_objs.append(Registro(
                    id_pregunta=pregunta,
                    id_estudiante=estudiante,
                    opcion_seleccionada=opcion,
                    calificacion_obtenida=1
                ))
                etapa_actual = pregunta.id_etapa

        except (Pregunta.DoesNotExist, OpcionMultiple.DoesNotExist):
            continue

    # Respuesta Final Etapa 1
    if len(errores) > 0:
        return JsonResponse({
            "ok": False,
            "errores": errores,
            "msg": "Hay respuestas incorrectas."
        })
    else:
        # Si no hubo errores, pero tampoco respuestas válidas de selección múltiple
        if not correctas_objs:
             return JsonResponse({"error": "No se recibieron datos válidos para procesar."}, status=400)

        # Recopilar retroalimentación positiva
        aciertos_info = []
        for reg in correctas_objs:
            aciertos_info.append({
                "pregunta_id": reg.id_pregunta.id,
                "retro": reg.opcion_seleccionada.retroalimentacion or "¡Correcto!"
            })

        # Guardar en Transacción
        with transaction.atomic():
            # Borrar intentos previos de estas mismas preguntas
            preguntas_ids = [r.id_pregunta.id for r in correctas_objs]
            Registro.objects.filter(id_estudiante=estudiante, id_pregunta__id__in=preguntas_ids).delete()
            
            # Crear nuevos registros
            Registro.objects.bulk_create(correctas_objs)
            
            if etapa_actual:
                EtapaCompletada.objects.get_or_create(estudiante=estudiante, etapa=etapa_actual)

        return JsonResponse({
            "ok": True,
            "aciertos": aciertos_info,
            "msg": "Etapa completada."
        })

@csrf_exempt
def guardar_exploracion(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    estudiante_id = request.POST.get("estudiante_id")
    exploracion_id = request.POST.get("exploracion_id")
    texto = request.POST.get("texto_respuesta", "").strip()

    if not estudiante_id or not exploracion_id:
        return JsonResponse({"error": "Faltan datos"}, status=400)

    # Buscar estudiante y exploración
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
        exploracion = Exploracion.objects.get(id=exploracion_id)
        etapa = exploracion.id_etapa
    except:
        return JsonResponse({"error": "Objeto no encontrado"}, status=404)

    # Guardar/Actualizar respuesta
    Registro.objects.update_or_create(
        id_estudiante=estudiante,
        id_exploracion=exploracion,
        defaults={"respuesta_texto_libre": texto},
    )

    # Verificar si completó todas las exploraciones
    total = etapa.exploraciones.count()
    respondidas = Registro.objects.filter(
        id_estudiante=estudiante,
        id_exploracion__in=etapa.exploraciones.all()
    ).count()

    etapa_completa = (respondidas == total)

    # Si completó la etapa → marcarla como completada
    if etapa_completa:
        EtapaCompletada.objects.get_or_create(
            estudiante=estudiante,
            etapa=etapa
        )

    return JsonResponse({
        "ok": True,
        "etapa_completa": etapa_completa,
        "msg": "Respuesta guardada correctamente."
    })