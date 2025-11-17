from django.urls import path
from .views import (
    ListaPacientesPorCursoView,
    DetallePacienteView,
    VistaEtapaView,
    validar_respuesta_ajax
)

app_name = 'casos'

urlpatterns = [
    path('curso/<int:id_curso>/', ListaPacientesPorCursoView.as_view(), name='lista_casos'),
    path('paciente/<int:id_paciente>/', DetallePacienteView.as_view(), name='detalle_paciente'),

    # Nueva vista de etapa
    path('paciente/<int:id_paciente>/etapa/<int:numetapa>/', 
         VistaEtapaView.as_view(), name='detalle_etapa'),

    # AJAX validator
    path('validar-respuesta/', validar_respuesta_ajax, name='validar_respuesta'),
]