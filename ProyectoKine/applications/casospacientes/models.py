from django.db import models
from applications.cursosdocente.models import Curso

class Paciente(models.Model):
    id_curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    nombre_caso = models.CharField("Nombre Caso", max_length=200)
    tipo_de_caso = models.CharField("Tipo de Caso", max_length=150)
    descripcion = models.TextField("Descripción del caso")
    url_video = models.URLField("URL video")
    pregunta = models.TextField("Pregunta")

    def __str__(self):
        return f"{self.nombre_caso} <{self.id}>"

class Diagnostico(models.Model):
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha_creacion = models.DateField("Fecha de Creación",auto_now_add=True)
    nombre_formulario = models.CharField("Nombre Formulario",max_length=150)
    descripcion = models.TextField("Descripción del formulario") 

    def __str__(self):
        return f"Diagnóstico {self.id} para {self.id_paciente.nombre_caso}"

class Respuesta(models.Model):
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    id_diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    correcta_incorrecta = models.BooleanField()
    respuesta_correcta = models.TextField("Respuesta correcta")
    retroalimentacion = models.TextField("Retroalimentación")

    def __str__(self):
        return f"Respuesta {self.id} para {self.id_paciente.nombre_caso}"
