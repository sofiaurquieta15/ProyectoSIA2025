from django.db import models
from applications.login.models import Estudiante  # Import de Estudiante model
from applications.login.models import Docente
from applications.cursosdocente.models import Curso
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

class TipoCaso(models.Model):
    nombre = models.CharField("Tipo de Caso", max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Paciente(models.Model):
    nombre = models.CharField("Nombre del Paciente", max_length=255)
    edad = models.PositiveSmallIntegerField("Edad (Años)", help_text="usar 0 para lactantes (< 1 año)", validators=[MaxValueValidator(110)])
    sexo = models.CharField(
        "Sexo",
        max_length=20,
        choices=[
            ("Masculino", "Masculino"),
            ("Femenino", "Femenino"),
            ("Otro", "Otro"),
        ]
    )
    ocupacion = models.CharField("Ocupación", max_length=255)
    descripcion = models.TextField("Descripción del Paciente")
    tipo_caso = models.ForeignKey(TipoCaso, on_delete=models.CASCADE)
    id_curso = models.ForeignKey('cursosdocente.Curso', on_delete=models.CASCADE)
    visible = models.BooleanField("Visible para estudiantes", default=False)
    completo = models.BooleanField("Caso Terminado (3 etapas)", default=False)

    def __str__(self):
        return self.nombre

class Etapa(models.Model):
    TIPO_ETAPA = [
        ("MULTIPLE", "Selección Múltiple (Etapa 1)"),
        ("EXPLORACIONES", "Exploraciones Clínicas (Etapa 2)"),
        ("ESCRITA", "Respuesta Escrita (Etapa 3)"),
    ]

    nombreetapa = models.CharField("Nombre Etapa", max_length=100)
    numetapa = models.IntegerField("Número de Etapa", validators=[MinValueValidator(1), MaxValueValidator(3)], help_text="Ingrese un número del 1 al 3.")
    id_paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

    tipo_pregunta = models.CharField(
        "Tipo de Etapa",
        max_length=20,
        choices=TIPO_ETAPA,
        default="MULTIPLE"
    )

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ['id_paciente','numetapa']
        unique_together = ('id_paciente', 'numetapa')

    def __str__(self):
        return self.nombreetapa


class Pregunta(models.Model):
    TIPO_PREGUNTA_CHOICES = [
        ('MULTIPLE', 'Selección Múltiple'),
        ('ESCRITA', 'Respuesta Escrita'),
    ]

    docente = models.ForeignKey(
        'login.Docente',
        on_delete=models.CASCADE,
        related_name='preguntas_creadas'
    )

    id_etapa = models.ForeignKey(
        Etapa,
        on_delete=models.CASCADE,
        related_name='preguntas'
    )

    titulo = models.CharField("Título Pregunta", max_length=255)
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_PREGUNTA_CHOICES,
        verbose_name="Tipo de Pregunta"
    )

    # Nueva URL de video asociada a cada pregunta
    urlvideo = models.URLField("URL Video de la Pregunta", null=True, blank=True)

    clave_respuesta_escrita = models.TextField(
        "Clave de Corrección / Palabras clave",
        null=True,
        blank=True,
        help_text="Solo se usa si el tipo es 'Respuesta Escrita'."
    )
    retroalimentacion_general = models.TextField(
        "Retroalimentación General",
        null=True,
        blank=True,
        help_text="Mensaje que se muestra al estudiante al finalizar."
    )

    @property
    def embed_url(self):

        url = self.urlvideo
        if "watch?v=" in url:
            return url.replace("watch?v=","embed/")
        return url
    

    def save(self, *args, **kwargs):
        # Convertir URL tipo watch?v=
        if "watch?v=" in self.urlvideo:
            video_id = self.urlvideo.split("watch?v=")[1].split("&")[0]
            self.urlvideo = f"https://www.youtube.com/embed/{video_id}"

        # Convertir URL tipo youtu.be
        elif "youtu.be/" in self.urlvideo:
            video_id = self.urlvideo.split("youtu.be/")[1].split("?")[0]
            self.urlvideo = f"https://www.youtube.com/embed/{video_id}"

        super().save(*args, **kwargs)

    def __str__(self):
        # CAMBIO AQUÍ: Ahora muestra [NOMBRE PACIENTE] Título de pregunta
        paciente_nombre = "Sin Paciente"
        if self.id_etapa and self.id_etapa.id_paciente:
            paciente_nombre = self.id_etapa.id_paciente.nombre
            
        return f"[{paciente_nombre}] {self.titulo}"

class Exploracion(models.Model):
    id_etapa = models.ForeignKey(
        Etapa,
        on_delete=models.CASCADE,
        related_name='exploraciones'
    )

    titulo = models.CharField("Título de la Exploración", max_length=255)
    instruccion = models.TextField(
        "Texto / Pregunta de la Exploración",
        help_text="Por ejemplo: 'Describe la exploración a realizar en esta zona'."
    )

    urlvideo = models.URLField("URL Video de la Exploración")

    orden = models.PositiveSmallIntegerField(
        "Orden",
        help_text="Número de botón (1 a 6).",
    )

    retroalimentacion_general = models.TextField(
        "Retroalimentación General",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Exploración"
        verbose_name_plural = "Exploraciones"
        ordering = ['id_etapa', 'orden']
        unique_together = ('id_etapa', 'orden')  # para que no tengas dos “PARTE EXP 1” en la misma etapa

    def __str__(self):
        return f"{self.id_etapa} - Parte {self.orden}: {self.titulo}"
    
    def clean(self):
        if not self.pk and self.id_etapa_id:
            cantidad_actual = Exploracion.objects.filter(id_etapa=self.id_etapa).count()
            if cantidad_actual >= 6:
                raise ValidationError("Límite alcanzado: No se pueden agregar más de 6 exploraciones por etapa.")
            super().clean()
            
    def embed_url(self):

        url = self.urlvideo
        if "watch?v=" in url:
            return url.replace("watch?v=","embed/")
        return url

    def save(self, *args, **kwargs):
        # MISMA lógica de conversión a embed
        if self.urlvideo:
            if "watch?v=" in self.urlvideo:
                video_id = self.urlvideo.split("watch?v=")[1].split("&")[0]
                self.urlvideo = f"https://www.youtube.com/embed/{video_id}"
            elif "youtu.be/" in self.urlvideo:
                video_id = self.urlvideo.split("youtu.be/")[1].split("?")[0]
                self.urlvideo = f"https://www.youtube.com/embed/{video_id}"

        super().save(*args, **kwargs)

class OpcionMultiple(models.Model):
    pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        related_name='opciones',
        limit_choices_to={'tipo': 'MULTIPLE'},
        help_text="Pregunta a la que pertenece esta opción."
    )

    texto_opcion = models.CharField("Texto de la Opción", max_length=255)
    is_correct = models.BooleanField("Opción Correcta", default=False)
    retroalimentacion = models.TextField(
        "Retroalimentación Específica",
        blank=True,
        null=True,
        help_text="Mensaje solo si esta opción es seleccionada."
    )

    def __str__(self):
        return self.texto_opcion

    class Meta:
        verbose_name = "Opción Múltiple"
        verbose_name_plural = "Opciones Múltiples"
        unique_together = ('pregunta', 'texto_opcion')

class EtapaCompletada(models.Model):
    estudiante = models.ForeignKey('login.Estudiante', on_delete=models.CASCADE)
    etapa = models.ForeignKey(Etapa, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('estudiante', 'etapa')

    def __str__(self):
        return f"{self.estudiante} completó {self.etapa}"

class Registro(models.Model):
    # Para Preguntas normales (etapa 1 y 3)
    id_pregunta = models.ForeignKey(
        Pregunta,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Para Exploraciones (etapa 2)
    id_exploracion = models.ForeignKey(
        'casospacientes.Exploracion',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    id_estudiante = models.ForeignKey('login.Estudiante', on_delete=models.CASCADE)

    fecha_envio = models.DateTimeField("Fecha de Envío", auto_now_add=True)

    intentos_fallidos = models.PositiveSmallIntegerField(
        "Intentos Fallidos", 
        default=0,
        help_text="Contador de errores antes de acertar (para cálculo de puntaje)."
    )

    opcion_seleccionada = models.ForeignKey(
        OpcionMultiple,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Solo se usa si es una pregunta de selección múltiple."
    )

    respuesta_texto_libre = models.TextField(
        "Respuesta Texto Libre",
        blank=True,
        null=True,
        help_text="Texto escrito por el estudiante (pregunta escrita o exploración)."
    )

    def __str__(self):
        if self.id_pregunta:
            return f"Registro de {self.id_estudiante} en Pregunta {self.id_pregunta_id}"
        if self.id_exploracion:
            return f"Registro de {self.id_estudiante} en Exploración {self.id_exploracion_id}"
        return f"Registro de {self.id_estudiante}"