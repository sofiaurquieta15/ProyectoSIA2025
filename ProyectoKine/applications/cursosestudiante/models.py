from django.db import models
from applications.login.models import Estudiante, Docente
from applications.cursosdocente.models import Curso
from applications.casospacientes.models import Registro, Paciente, Exploracion

# Create your models here.

class Enrolamiento(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='enrolamientos')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='enrolamientos')
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name='enrolamientos')
    fecha_inscripcion = models.DateTimeField("Fecha de Inscripción", auto_now_add=True)

    def __str__(self):
        return f"{self.estudiante.nombre} - {self.curso.nombrecurso} - {self.docente.nombre_docente}"

    class Meta:
        verbose_name = "Enrolamiento"
        verbose_name_plural = "Enrolamientos"
        ordering = ['fecha_inscripcion']

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

class SolicitudRevision(models.Model):
    TIPO_ETAPA = [
        (2, 'Exploración Física'),
        (3, 'Diagnóstico'),
    ]
    
    ESTADO_SOLICITUD = [
        ('PENDIENTE', 'Pendiente'),
        ('RESPONDIDA', 'Respondida'),
    ]

    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    
    # Etapa que se quiere revisar (2 o 3)
    etapa_solicitud = models.IntegerField("Etapa a Revisar", choices=TIPO_ETAPA)
    
    # Opcional: Si es etapa 2, puede especificar qué exploración. Si es etapa 3, esto queda null.
    exploracion_especifica = models.ForeignKey(Exploracion, on_delete=models.CASCADE, null=True, blank=True)

    motivo = models.TextField("Motivo de revisión")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    # Campos para la respuesta del docente (se llenarán después)
    estado = models.CharField(max_length=20, choices=ESTADO_SOLICITUD, default='PENDIENTE')
    respuesta_docente = models.TextField("Retroalimentación del Docente", null=True, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Solicitud de {self.estudiante.nombre} - {self.paciente.nombre} - Etapa {self.etapa_solicitud}"

    class Meta:
        verbose_name = "Solicitud de Revisión"
        verbose_name_plural = "Solicitudes de Revisión"
        ordering = ['-fecha_solicitud']