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
        unique_together = ('kinesiología', 'id_docente')

    def __str__(self):
        return self.nombrecurso
