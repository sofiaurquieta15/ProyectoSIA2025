from django.db import models
from applications.login.models import Estudiante
from applications.cursosdocente.models import Curso
from applications.casospacientes.models import Respuesta

# Create your models here.

class Avance(models.Model):
    id_curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    fecha_actualizacion = models.DateField("Fecha de Actualización", auto_now_add=True)
    porcentaje_avance = models.DecimalField("Porcentaje de Avance", max_digits=5, decimal_places=2)

    def _str_(self):
        return f"Avance de {self.id_estudiante.nombre} en {self.id_curso.nombre_clase}"

class RespuestaEstudiante(models.Model):
    id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    id_respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE)
    respuesta_seleccionada = models.TextField("Respuesta del Estudiante")
    fecha_envio = models.DateField("Fecha de envío de respuesta", auto_now_add=True)

    def _str_(self):
        return f"Respuesta de {self.id_estudiante.nombre}"