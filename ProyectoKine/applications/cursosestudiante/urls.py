from django.urls import path
from . import views

app_name = 'cursosestudiante'

urlpatterns = [
    path('menu-estudiante/', views.menu_estudiante, name='menu_estudiante'),
    path('mis-cursos/', views.ListaCursosEstudianteView.as_view(), name='lista_cursos'),
    path('avances/', views.RevisarAvancesView, name='ver_avances'),
    path('solicitar-revision/', views.SolicitudRevisionView, name='solicitar_revision'),
    path('api/crear-solicitud/', views.crear_solicitud_ajax, name='crear_solicitud_ajax'),
    path('estado-solicitudes/', views.EstadoSolicitudesView, name='estado_solicitudes'),
]