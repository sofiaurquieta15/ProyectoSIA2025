from django.urls import path
from . import views 

app_name = 'cursos'

urlpatterns = [
    # Vistas anteriores
    path('menu-docente/', views.MenuDocenteView, name='menu_docente'),
    
    # --- NUEVO MÓDULO DE GESTIÓN (Agrega todo esto) ---
    path('mis-cursos/', views.GestionCursosDocenteView, name='mis_cursos'), # Vista gestión cursos
    path('enrolar-estudiante/', views.enrolar_estudiante, name='enrolar_estudiante'),
    path('desenrolar-estudiante/', views.desenrolar_estudiante, name='desenrolar_estudiante'),
    path('revisiones/', views.RevisionesDocenteView, name='revisiones_docente'),

    path('detalle-intentos/<int:estudiante_id>/<int:etapa_id>/', views.obtener_detalle_intentos, name='detalle_intentos'),
    
    # Vista Principal de Gestión de Casos (La de las 3 tarjetas grandes)
    path('gestion-casos/', views.GestionCasosView, name='gestion_casos'),
    
    # Rutas para Configuración de Etapas
    path('configurar-etapas/<int:paciente_id>/', views.ConfigurarEtapasView, name='configurar_etapas'),

    # APIs AJAX (Para que los formularios funcionen sin recargar)
    # Creación
    path('api/crear-curso/', views.crear_curso_ajax, name='crear_curso_ajax'),
    path('api/crear-tipo-caso/', views.crear_tipo_caso_ajax, name='crear_tipo_caso_ajax'),
    path('api/crear-paciente/', views.crear_paciente_ajax, name='crear_paciente_ajax'),
    
    # Edición y Eliminación
    path('api/eliminar/<str:modelo>/<int:pk>/', views.eliminar_objeto_ajax, name='eliminar_objeto'),
    path('api/obtener/<str:modelo>/<int:pk>/', views.obtener_datos_edicion, name='obtener_datos'),
    path('api/guardar/<str:modelo>/<int:pk>/', views.guardar_edicion_ajax, name='guardar_edicion'),

    # Guardado de contenido de etapas
    path('api/guardar-pregunta/', views.guardar_pregunta_etapa, name='guardar_pregunta_etapa'),
    path('api/guardar-exploracion/', views.guardar_exploracion_etapa, name='guardar_exploracion_etapa'),
    path('api/guardar-diagnostico/', views.guardar_diagnostico_etapa, name='guardar_diagnostico_etapa'),

    path('api/eliminar-pregunta/<int:pk>/', views.eliminar_pregunta_api, name='eliminar_pregunta_api'),
    path('api/obtener-pregunta/<int:pk>/', views.obtener_pregunta_api, name='obtener_pregunta_api'),

    path('api/eliminar-exploracion/<int:pk>/', views.eliminar_exploracion_api, name='eliminar_exploracion_api'),
    path('api/obtener-exploracion/<int:pk>/', views.obtener_exploracion_api, name='obtener_exploracion_api'),

    path('api/guardar-diagnostico/', views.guardar_diagnostico_etapa, name='guardar_diagnostico_etapa'),
    path('api/obtener-diagnostico/<int:pk>/', views.obtener_diagnostico_api, name='obtener_diagnostico_api'),
    path('api/eliminar-diagnostico/<int:pk>/', views.eliminar_diagnostico_api, name='eliminar_diagnostico_api'),

    path('api/toggle-visibilidad/<int:pk>/', views.toggle_visibilidad_paciente, name='toggle_visibilidad'),
    path('api/eliminar-registros/', views.eliminar_registros_api, name='eliminar_registros_api'),
]