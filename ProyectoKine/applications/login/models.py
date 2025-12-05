from django.db import models
from django.core.exceptions import ValidationError

def validar_correo_alumno(value):
    if not value.endswith("@alumnos.ucn.cl"):
        raise ValidationError("El correo debe terminar en @alumnos.ucn.cl")
    
def validar_correo_docente(value):
    dominios_permitidos = ["@ucn.cl", "@ce.ucn.cl"]
    if not any(value.endswith(dominio) for dominio in dominios_permitidos):
        raise ValidationError("El correo debe ser @ucn.cl o @ce.ucn.cl")


class Docente(models.Model):
    nombre_docente = models.CharField("Nombre Docente",max_length=150,null=False, blank=True)
    apellido_docente = models.CharField("Apellido Docente", max_length=150,null=False, blank=True)
    correo_docente = models.EmailField("Email Docente", unique=True, validators=[validar_correo_docente])
    passw_docente = models.CharField("Contraseña Docente", max_length=25, null=False, default='123456')
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre_docente} <{self.correo_docente}>"
    
    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ['nombre_docente']

class Estudiante(models.Model):
    nombre = models.CharField("Nombre Estudiante", max_length=150, null=False, blank=True)
    apellido = models.CharField("Apellido Estudiante", max_length=150, null=False, blank=True)
    correo_institucional = models.EmailField("Email Estudiante", unique=True, validators=[validar_correo_alumno])
    passw_estudiante = models.CharField("Contraseña Estudiante", max_length=25, null=False, default='123456')
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} <{self.correo_institucional}>"
    
    class Meta:
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ['nombre']

   