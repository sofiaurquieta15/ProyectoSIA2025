from django.urls import path
from . import views 

app_name = 'cursos'

urlpatterns = [

    path('lista/',views.ListaCursosEstudianteView.as_view(), name='lista_cursos'),
    ]