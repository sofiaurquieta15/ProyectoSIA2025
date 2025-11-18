from django.views.generic import ListView
from applications.cursosdocente.models import Curso
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Paciente, Etapa, Pregunta, OpcionMultiple, Registro
from applications.login.models import Estudiante

class ListaPacientesPorCursoView(ListView):
    model = Paciente
    template_name = 'casospacientes/lista_casos.html'
    context_object_name = 'pacientes'

    def get_queryset(self):
        id_curso = self.kwargs['id_curso']
        return Paciente.objects.filter(id_curso=id_curso)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['curso'] = Curso.objects.get(id=self.kwargs['id_curso'])
        return context

class DetallePacienteView(TemplateView):
    template_name = 'casospacientes/detalle_paciente.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        paciente = Paciente.objects.get(id=self.kwargs['id_paciente'])
        etapas = Etapa.objects.filter(id_paciente=paciente)

        context['paciente'] = paciente
        context['etapas'] = etapas

        return context

class VistaEtapaView(TemplateView):
    template_name = 'casospacientes/etapa.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        id_paciente = kwargs['id_paciente']
        numetapa = kwargs['numetapa']

        etapa = get_object_or_404(Etapa, id_paciente=id_paciente, numetapa=numetapa)
        
        # 🔥 Ahora trae TODAS las preguntas de la etapa
        preguntas = Pregunta.objects.filter(id_etapa=etapa).prefetch_related("opciones")

        paciente = Paciente.objects.get(id=id_paciente)
        total_etapas = Etapa.objects.filter(id_paciente=paciente).count()

        context.update({
            'etapa': etapa,
            'preguntas': preguntas,
            'paciente': paciente,
            'num_etapa': numetapa,
            'ultima_etapa': numetapa == total_etapas,
        })

        return context

@csrf_exempt
def validar_respuesta_ajax(request):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    opcion_id = request.POST.get("opcion_id")
    texto_respuesta = request.POST.get("texto_respuesta", "").strip()
    pregunta_id = request.POST.get("pregunta_id")
    estudiante_id = request.POST.get("estudiante_id")

    # Validar pregunta
    try:
        pregunta = Pregunta.objects.get(id=pregunta_id)
    except Pregunta.DoesNotExist:
        return JsonResponse({"error": "Pregunta no existe"}, status=400)

    # Validar estudiante
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return JsonResponse({"error": "Estudiante no existe"}, status=400)

    # ======================================================
    # =============   SELECCIÓN MÚLTIPLE   =================
    # ======================================================
    if opcion_id:
        try:
            opcion = OpcionMultiple.objects.get(id=opcion_id)
        except OpcionMultiple.DoesNotExist:
            return JsonResponse({"error": "Opción no existe"}, status=400)

        Registro.objects.create(
            id_pregunta=pregunta,
            id_estudiante=estudiante,
            opcion_seleccionada=opcion,
            calificacion_obtenida=1 if opcion.is_correct else 0
        )

        return JsonResponse({
            "correcto": opcion.is_correct,
            "retroalimentacion": opcion.retroalimentacion or "",
            "retroalimentacion_general": pregunta.retroalimentacion_general or ""
        })

    # ======================================================
    # ================   RESPUESTA ESCRITA   =================
    # ======================================================
    if texto_respuesta:
        Registro.objects.create(
            id_pregunta=pregunta,
            id_estudiante=estudiante,
            respuesta_texto_libre=texto_respuesta,
            calificacion_obtenida=1
        )

        return JsonResponse({
            "correcto": True,
            "retroalimentacion": pregunta.retroalimentacion_general or "",
            "retroalimentacion_general": pregunta.retroalimentacion_general or ""
        })

    return JsonResponse({"error": "Datos insuficientes"}, status=400)