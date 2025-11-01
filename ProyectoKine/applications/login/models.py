from django.db import models

class Docente(models.Model):
    nombre_docente=models.CharField("Nombre Docente",max_length=150,null=False)
    correo_docente = models.EmailField("Email Docente", unique=True)
    passw_docente = models.CharField("Contraseña Docente", max_length=25, null=False)

    def __str__(self):
        return f"{self.nombre_docente} <{self.correo_docente}>"

class Estudiante(models.Model):
    nombre = models.CharField("Nombre Estudiante", max_length=150, null=False)
    correo_institucional = models.EmailField("Email Estudiante", unique=True)
    passw_estudiante = models.CharField("Contraseña Estudiante", max_length=25, null=False)

    def __str__(self):
        return f"{self.nombre} <{self.correo_institucional}>"