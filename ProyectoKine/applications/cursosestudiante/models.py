from django.db import models
from applications.login.models import Estudiante
from applications.cursosdocente.models import Curso
from applications.casospacientes.models import Registro

# Create your models here.

class Avance(models.Model):
    # Relacionado con el estudiante
    id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    # Relacionado con el curso
    id_curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    # Avance del estudiante en el curso (porcentaje)
    porcentajeavance = models.DecimalField("Porcentaje de Avance", max_digits=5, decimal_places=2)
    # Fecha de la última actualización de avance
    fecha_actualizacion = models.DateTimeField("Fecha de Actualización")
    # Indica si el curso está completado o no
    completado = models.BooleanField("Completado", default=False)
    # Relacionado con las respuestas seleccionadas por el estudiante (modelo Registro)
    respuestas = models.ManyToManyField(Registro, related_name='avances', blank=True)

    def __str__(self):
        return f"Avance de {self.id_estudiante.nombre} en {self.id_curso.nombrecurso}: {self.porcentajeavance}%"