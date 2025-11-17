from django.urls import path
from . import views 

app_name = 'login'

urlpatterns = [

    path('',views.InicioLoginView.as_view(), name='inicio'),

    path('estudiante/', views.LoginEstudianteView.as_view(), name='login_estudiante'),
    path('docente/',views.LoginDocenteView.as_view(), name='login_docente'),
]