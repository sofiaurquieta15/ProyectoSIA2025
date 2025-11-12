from django.db import models
from applications.login.models import Estudiante  # Import the Estudiante model
from applications.cursosdocente.models import Curso

class Paciente(models.Model):
    titulopaciente = models.CharField("Título Paciente", max_length=255)
    descpaciente = models.TextField("Descripción del Paciente")
    categoriapaciente = models.CharField("Categoría Paciente", max_length=100)
    id_curso = models.ForeignKey('cursosdocente.Curso', on_delete=models.CASCADE)

    def __str__(self):
        return self.titulopaciente

class Etapa(models.Model):
    nombreetapa = models.CharField("Nombre Etapa", max_length=100)
    numetapa = models.IntegerField("Número de Etapa")  # 1, 2, or 3
    urlvideo = models.URLField("URL Video")
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

    def __str__(self):
        return f"Etapa {self.numetapa}: {self.nombreetapa}"

class TipoPregunta(models.Model):
    nombretipo = models.CharField("Tipo de Pregunta", max_length=50)

    def __str__(self):
        return self.nombretipo

class Pregunta(models.Model):
    titulopregunta = models.CharField("Título Pregunta", max_length=255)
    id_etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)
    id_tipo = models.ForeignKey(TipoPregunta, on_delete=models.CASCADE)

    def __str__(self):
        return self.titulopregunta

class Respuesta(models.Model):
    respuesta_text = models.TextField("Respuesta (Texto)")
    respuesta_bool = models.BooleanField("Respuesta (Alternativa)")
    retroalimentacion = models.TextField("Retroalimentación")
    is_correct = models.BooleanField("Es Correcta?")
    id_pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)

    def __str__(self):
        return f"Respuesta: {self.id_pregunta.titulopregunta}"

class Registro(models.Model):
    respuestaselect = models.CharField("Respuesta Seleccionada", max_length=255)
    fechaenvio = models.DateTimeField("Fecha de Envío")
    id_respuesta = models.ForeignKey(Respuesta, on_delete=models.CASCADE)
    id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)

    def __str__(self):
        return f"Registro de {self.id_estudiante.nombre} - {self.respuestaselect}"

