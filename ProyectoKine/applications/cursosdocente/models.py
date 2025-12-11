from django.db import models
from applications.login.models import Docente

class Curso(models.Model):
    nombrecurso = models.CharField("Nombre del Curso", max_length=255)
    objetivos = models.TextField("Objetivos del Curso")
    fechacreacion = models.DateTimeField("Fecha de Creación")
    id_docente = models.ForeignKey(Docente, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ['nombrecurso']

    def __str__(self):
        return self.nombrecurso

class NotificacionDocenteVista(models.Model):
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE)
    solicitud_id = models.IntegerField() # Guardamos el ID de la solicitud vista
    fecha_vista = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('docente', 'solicitud_id')
        verbose_name = "Notificación Docente Vista"
        verbose_name_plural = "Notificaciones Docente Vistas"
