from django.urls import path
from . import views 

app_name = 'cursos'

urlpatterns = [

    path('lista/',views.ListaCursosEstudianteView.as_view(), name='lista_cursos'),
    path('listado/', views.ListaCursosView.as_view(), name='listado_cursos'),
    path('crear/', views.CursoCreateView.as_view(),name='crear_cursos'),
    ]