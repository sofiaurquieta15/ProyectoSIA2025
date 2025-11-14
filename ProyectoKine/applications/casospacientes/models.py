from django.db import models
from applications.login.models import Estudiante  # Import de Estudiante model
from applications.login.models import Docente
from applications.cursosdocente.models import Curso

class Paciente(models.Model):
    titulopaciente = models.CharField("Título Paciente", max_length=255)
    descpaciente = models.TextField("Descripción del Paciente")
    categoriapaciente = models.CharField("Categoría Paciente", max_length=100)
    id_curso = models.ForeignKey('cursosdocente.Curso', on_delete=models.CASCADE)

    def _str_(self):
        return self.titulopaciente

class Etapa(models.Model):
    nombreetapa = models.CharField("Nombre Etapa", max_length=100)
    numetapa = models.IntegerField("Número de Etapa")
    urlvideo = models.URLField("URL Video")
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

    def _str_(self):
        return f"Etapa {self.numetapa}: {self.nombreetapa}"
    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ['id_paciente','numetapa'] 
        unique_together = ('id_paciente', 'numetapa') #esto permite que un paciente no pueda tener la misma etapa dos veces
        

class Pregunta(models.Model):
    TIPO_PREGUNTA_CHOICES = [
        ('MULTIPLE', 'Selección Múltiple'),
        ('ESCRITA', 'Respuesta Escrita'),
    ]

    # Vínculos y metadatos
    docente = models.ForeignKey(
        'login.Docente', # Asumo esta ubicación para el modelo Docente
        on_delete=models.CASCADE,
        related_name='preguntas_creadas'
    )
    id_etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)

    # Contenido de la pregunta
    titulo = models.CharField("Título Pregunta", max_length=255)
    texto = models.TextField("Texto de la Pregunta")
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_PREGUNTA_CHOICES,
        verbose_name="Tipo de Pregunta"
    )
    puntuacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    # Clave de Corrección (Solo para Respuesta Escrita)
    clave_respuesta_escrita = models.TextField(
        "Clave de Corrección / Palabras clave",
        null=True,
        blank=True,
        help_text="Texto o palabras clave esperadas. Solo se usa si el tipo es 'Respuesta Escrita'."
    )
    retroalimentacion_general = models.TextField(
        "Retroalimentación General",
        null=True,
        blank=True,
        help_text="Mensaje que se muestra al estudiante sin importar su respuesta."
    )

    def _str_(self):
        return f"[{self.get_tipo_display()}] {self.titulo}"
    
    class Meta:
        verbose_name_plural = "Preguntas"

class OpcionMultiple(models.Model):
    """
    Representa una de las 4 alternativas posibles para una pregunta de Selección Múltiple.
    """
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='opciones',
        limit_choices_to={'tipo': 'MULTIPLE'}, # Opcional: filtro para el Admin/Forms
        help_text="Pregunta a la que pertenece esta opción."
    )
    texto_opcion = models.CharField("Texto de la Opción", max_length=255)
    is_correct = models.BooleanField("Opción Correcta", default=False)
    retroalimentacion = models.TextField(
        "Retroalimentación Específica",
        blank=True,
        null=True,
        help_text="Mensaje solo para si esta opción es seleccionada."
    )

    def _str_(self):
        return self.texto_opcion

    class Meta:
        verbose_name = "Opción Múltiple"
        verbose_name_plural = "Opciones Múltiples"
        # Garantiza que no haya dos opciones con el mismo texto para la misma pregunta
        unique_together = ('pregunta', 'texto_opcion') 

class Registro(models.Model):
    """
    Almacena la respuesta de un estudiante a una pregunta específica.
    """
    # Vínculos
    id_pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    id_estudiante = models.ForeignKey('login.Estudiante', on_delete=models.CASCADE) # Asumo esta ubicación
    
    # Metadatos
    fecha_envio = models.DateTimeField("Fecha de Envío", auto_now_add=True)
    calificacion_obtenida = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Puntuación asignada a esta respuesta."
    )

    # Contenido de la Respuesta del Estudiante (mutuamente excluyentes)
    opcion_seleccionada = models.ForeignKey(
        OpcionMultiple,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="ID de la OpcionMultiple seleccionada (si es tipo MÚLTIPLE)."
    )
    respuesta_texto_libre = models.TextField(
        "Respuesta Texto Libre",
        blank=True,
        null=True,
        help_text="Texto escrito por el estudiante (si es tipo ESCRITA)."
    )

    def _str_(self):
        return f"Registro de {self.id_estudiante.nombre} en {self.id_pregunta.titulo}"
