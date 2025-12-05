from django.urls import path 
from . import views
from .views import LoginEstudianteView, LoginDocenteView, logout_view

app_name = 'login'

urlpatterns = [

    path('',views.InicioLoginView.as_view(), name='inicio'),

    path('estudiante/', views.LoginEstudianteView.as_view(), name='login_estudiante'),
    path('docente/',views.LoginDocenteView.as_view(), name='login_docente'),
    path('logout/', logout_view, name='logout'),

    path('editar-perfil-docente/', views.editar_perfil_docente, name='editar_perfil_docente'),

    path('editar-perfil-estudiante/', views.editar_perfil_estudiante, name='editar_perfil_estudiante'),
]
