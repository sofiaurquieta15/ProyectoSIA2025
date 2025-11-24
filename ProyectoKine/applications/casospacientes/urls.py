from django.urls import path
from .views import (
    ListaPacientesPorCursoView,
    DetallePacienteView,
    VistaEtapaView,
    VistaEtapa2View,
    VistaEtapa3View,
    validar_respuesta_ajax,
    guardar_exploracion,
)

app_name = 'casos'

urlpatterns = [
    path('curso/<int:id_curso>/', ListaPacientesPorCursoView.as_view(), name='lista_casos'),

    path('paciente/<int:id_paciente>/', DetallePacienteView.as_view(), name='detalle_paciente'),

    # ETAPA 1
    path('paciente/<int:id_paciente>/etapa/<int:numetapa>/', 
         VistaEtapaView.as_view(), name='detalle_etapa'),

    # ETAPA 2
    path('paciente/<int:id_paciente>/etapa2/<int:numetapa>/',
         VistaEtapa2View.as_view(), name='detalle_etapa2'),

    # ETAPA 3
    path('paciente/<int:id_paciente>/etapa3/<int:numetapa>/', VistaEtapa3View.as_view(), name='detalle_etapa3'
),

    # AJAX
    path('validar-respuesta/', validar_respuesta_ajax, name='validar_respuesta'),

    path('guardar-exploracion/', guardar_exploracion, name='guardar_exploracion'),
]
