# KineLearn
Plataforma educativa interactiva para el aprendizaje de Kinesiología en la Universidad Católica del Norte.
## Descripción
**KineLearn** es un sistema de apoyo educativo desarrollado para la carrera de Kinesiología de la Universidad Católica del Norte (UCN). Su objetivo es optimizar el proceso de enseñanza y aprendizaje mediante la digitalización de clases, módulos interactivos y formularios de diagnóstico clínico.
La plataforma permite a los docentes crear, administrar y evaluar contenido educativo —como videos, formularios y preguntas interactivas—, mientras que los estudiantes pueden acceder a clases, completar módulos prácticos y recibir retroalimentación personalizada.
Desarrollado bajo un enfoque ágil SCRUMBAN, KineLearn busca integrar la tecnología en la formación académica, garantizando una experiencia intuitiva, accesible y segura que fortalece las competencias prácticas de los futuros kinesiólogos
## Integrantes y roles del equipo
- Jalil Ahure Cortés - Scrum Master
- Denis Baez Fuentes - Product Owner
- Constanza Torres Aguilera
- Melany Torres Zarricueta
- Nicolle Uceda Vega
- Sofia Urquieta Palma
- Millaray Zalazar Maluenda
## Instrucciones de instalación y ejecución
El proyecto ofrece dos métodos de ejecución: 1.**local** (usando entorno virtual y PostgreSQL) o 2. **mediante contenedores** (usando Docker).

## Opción 1: Instalación Local (Python/PostgreSQL)
- ***Requisitos: tener Python instalado y Postgresql***
1. Clonar el repositorio:
   Descargar el repositorio (ya sea descargando el ZIP o clonando la URL).
2. Crear y activar un entorno virtual:
   utilice el comando: python -m venv .entorno 
3. Entrar al terminal
4. Crear dependencias, use librerías: django, psycopg2 y django-jazzmin.
5. Configurar PostgreSQL:
   5.1 Crear la base de datos: CREATE DATABASE db_kinelearn;
   5.2 Crear el usuario: CREATE USER user_admin;
   5.3 Asignar contraseña al usuario: ALTER ROLE user_admin WITH PASSWORD '1234';
   5.4 Conectar a la DB: \c db_kinelearn;
   5.6 Crear schemas y permisos: GRANT USAGE ON SCHEMA public TO user_admin; | GRANT CREATE ON SCHEMA public TO user_admin;
6. Migrar la base de datos en la terminal
   Utilice los siguientes comandos, uno a la vez:
   python manage.py makemigrations
   python manage.py migrate
7. Crear un superusuario y cargar los datos iniciales
   python manage.py createsuperuser
8. Ejecutar el servidor
   python manage.py runserver

## Opción 2: Instalación Mediante Contenedores (Recomendado)
- ***Requisitos: tener Docker instalado y y el motor de contenedores en estado "running"***
1.Entrar al terminal en la carpeta principal del proyecto
2. Creación del archivo de variables de entorno (.env):
3. Dentro del nuevo archivo, crear configuraciones y credenciales de la base de datos:
  **Configuración del Proyecto**
  DJANGO_SETTINGS_MODULE=ProyectoKine.settings.deploy
  DEBUG=False
  ALLOWED_HOSTS=localhost,127.0.0.1
  **Credenciales de PostgreSQL para Docker**
  **POSTGRES_HOST debe coincidir con el nombre del servicio en docker-compose.yml**
  POSTGRES_DB=db_proyectokine
  POSTGRES_USER=user_proyectokine
  POSTGRES_PASSWORD=123456
  POSTGRES_HOST=db
  POSTGRES_PORT=5432
4. Ejecución y Despliegue de Docker en el terminal
  Utilizar el comando: docker-compose up –build
-	NO CIERRES ESTE TERMINAL
5. Ejecutar Migraciones y Recolectar Estáticos:
 	Abrir una nueva terminal y ejecutar los siguientes comandos, uno a la vez:
  **Ejecutar migraciones:**
  docker-compose exec web python manage.py migrate
  **Recolectar archivos estáticos:**
  docker-compose exec web python manage.py collectstatic --noinput
  **Crear Super Usuario:**
 	docker-compose exec web python manage.py createsuperuser
6. Acceder a la Aplicación:
 	Abre tu navegador y dirígete a: http://localhost:8000
7. Verificación:
 	Verificar que el proyecto y sus servicios (WEB y BD) aparezcan como activos en Docker Desktop.


## Datos de conexión de la base de datos
A continuación se muestran los parámetros de conexión utilizados por el proyecto **KineLearn**.  
*Los valores son de ejemplo y no representan credenciales reales.*
- **Tipo de base de datos:** PostgreSQL  
- **Host:** localhost  
- **Puerto:** 5432  
- **Nombre de la base de datos:** kinelearn_db  
- **Usuario:** kinelearn_user  
- **Contraseña:** ******** (no se expone públicamente)
