from django.db import models
from applications.login.models import Docente


class Curso(models.Model):
    nombre_clase = models.CharField("Nombre Curso", max_length=200,null=False)
    objetivos = models.TextField("Objetivos del curso")
    fecha_creacion = models.DateField("Fecha Creación Curso", auto_now_add=True)
    id_docente = models.ForeignKey(Docente, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre_clase} <{self.id}>"
