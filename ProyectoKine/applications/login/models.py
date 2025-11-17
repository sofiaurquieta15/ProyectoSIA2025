from django.db import models

class Docente(models.Model):
    nombre_docente = models.CharField("Nombre Docente",max_length=150,null=False, blank=True)
    correo_docente = models.EmailField("Email Docente", unique=True)
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
    correo_institucional = models.EmailField("Email Estudiante", unique=True)
    passw_estudiante = models.CharField("Contraseña Estudiante", max_length=25, null=False, default='123456')
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} <{self.correo_institucional}>"
    
    class Meta:
        verbose_name = "Estudiantes"
        verbose_name_plural = "Estudiantes"
        ordering = ['nombre']

   