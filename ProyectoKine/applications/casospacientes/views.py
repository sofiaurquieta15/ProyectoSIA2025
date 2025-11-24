import json
from django.views.generic import ListView, TemplateView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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

    estudiante_id = request.POST.get("estudiante_id")
    if not estudiante_id:
        return JsonResponse({"error": "Falta estudiante_id"}, status=400)

    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return JsonResponse({"error": "Estudiante no encontrado"}, status=404)

    # ------------------------------------------
    # ========== ETAPA 1 — SELECCIÓN MÚLTIPLE ==========
    # ------------------------------------------
    opcion_id = request.POST.get("opcion_id")
    pregunta_id = request.POST.get("pregunta_id")

    if opcion_id:
        try:
            pregunta = Pregunta.objects.get(id=pregunta_id)
            opcion = OpcionMultiple.objects.get(id=opcion_id)
            etapa = pregunta.id_etapa
        except:
            return JsonResponse({"error": "Pregunta u opción no válida"}, status=404)

        Registro.objects.create(
            id_pregunta=pregunta,
            id_estudiante=estudiante,
            opcion_seleccionada=opcion,
            calificacion_obtenida=1 if opcion.is_correct else 0
        )

        # Verificar si completó la etapa
        total = Pregunta.objects.filter(id_etapa=etapa).count()
        hechas = Registro.objects.filter(
            id_estudiante=estudiante,
            id_pregunta__id_etapa=etapa
        ).values("id_pregunta").distinct().count()

        if opcion.is_correct and hechas == total:
            EtapaCompletada.objects.get_or_create(
                estudiante=estudiante,
                etapa=etapa
            )

        return JsonResponse({
            "correcto": opcion.is_correct,
            "retro": opcion.retroalimentacion or "",
            "retroalimentacion_general": pregunta.retroalimentacion_general or ""
        })

    # ------------------------------------------
    # ========== ETAPA 2 — EXPLORACIONES ==========
    # ------------------------------------------
    exploracion_id = request.POST.get("exploracion_id")
    texto_resp = request.POST.get("texto_respuesta", "").strip()

    if exploracion_id:
        try:
            exp = Exploracion.objects.get(id=exploracion_id)
            etapa = exp.id_etapa
        except:
            return JsonResponse({"error": "Exploración no encontrada"}, status=404)

        if texto_resp == "":
            return JsonResponse({"error": "Debe escribir una respuesta."}, status=400)

        # Guardar/actualizar respuesta
        Registro.objects.update_or_create(
            id_estudiante=estudiante,
            id_exploracion=exp,
            defaults={"respuesta_texto_libre": texto_resp}
        )

        # Verificar si completó TODAS las exploraciones
        total = etapa.exploraciones.count()
        hechas = Registro.objects.filter(
            id_estudiante=estudiante,
            id_exploracion__in=etapa.exploraciones.all()
        ).count()

        etapa_completa = (total == hechas)

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

    # ------------------------------------------
    # ========== ETAPA 3 — RESPUESTA ESCRITA FINAL ==========
    # ------------------------------------------
    texto_final = request.POST.get("texto_respuesta", "").strip()

    if pregunta_id and texto_final:
        try:
            pregunta = Pregunta.objects.get(id=pregunta_id)
            etapa = pregunta.id_etapa
        except:
            return JsonResponse({"error": "Pregunta no encontrada"}, status=404)

        # Guardar respuesta — SOLO 1 VEZ
        registro, creado = Registro.objects.get_or_create(
            id_pregunta=pregunta,
            id_estudiante=estudiante,
            defaults={"respuesta_texto_libre": texto_final}
        )

        if not creado:
            return JsonResponse({
                "error": "La etapa ya fue respondida.",
                "bloqueado": True
            })

        # Marcar etapa completada
        EtapaCompletada.objects.get_or_create(
            estudiante=estudiante,
            etapa=etapa
        )

        return JsonResponse({
            "ok": True,
            "retro": pregunta.retroalimentacion_general or ""
        })

    # Si nada coincide
    return JsonResponse({"error": "Datos insuficientes"}, status=400)

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

