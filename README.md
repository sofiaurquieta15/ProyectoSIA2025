# KineLearn
Plataforma educativa interactiva para el aprendizaje de Kinesiología en la Universidad Católica del Norte.
## Descripción
**KineLearn** es un sistema de apoyo educativo desarrollado para la carrera de Kinesiología de la Universidad Católica del Norte (UCN). Su objetivo es optimizar el proceso de enseñanza y aprendizaje mediante la digitalización de clases, módulos interactivos y formularios de diagnóstico clínico.
La plataforma permite a los docentes crear, administrar y evaluar contenido educativo como videos, formularios y preguntas interactivas, mientras que los estudiantes pueden acceder a clases, completar módulos prácticos y recibir retroalimentación personalizada.
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
El proyecto ofrece dos métodos de ejecución: 1. **Mediante contenedores** (usando Docker) o 2. **Local** (usando entorno virtual y PostgreSQL) 

### Opción 1: Instalación Mediante Contenedores (Recomendado)
- ***Requisitos: tener Docker instalado y el motor de contenedores en estado "running"***
1. Entrar al terminal en la carpeta principal del proyecto
2. Creación del archivo de variables de entorno (.env):
3. Dentro del nuevo archivo, crear configuraciones y credenciales de la base de datos:
    - 3.1 **Configuración del Proyecto**
    -  DJANGO_SETTINGS_MODULE=ProyectoKine.settings.deploy
    -  DEBUG=False
    -  ALLOWED_HOSTS=localhost,127.0.0.1
    - 3.2 **Credenciales de PostgreSQL para Docker**
    - NOTA: POSTGRES_HOST debe coincidir con el nombre del servicio en docker-compose.yml
    -  POSTGRES_DB=db_proyectokine
    -  POSTGRES_USER=user_proyectokine
    -  POSTGRES_PASSWORD=123456
    -  POSTGRES_HOST=db
    -  POSTGRES_PORT=5432
4. Ejecución y Despliegue de Docker en el terminal
   - En la CMD ( a la altura del manage, no se ingresa al entorno) ejecuta los siguientes comandos: 
	        - docker-compose build
            - docker-compose up -d
    -  NOTA: no cierre esta terminal
6. Ejecutar Migraciones y Recolectar Estáticos:
   - 5.1 Abrir una nueva terminal y ejecutar los siguientes comandos, uno a la vez.
   - **Hacer las migraciones:**
   - docker-compose exec web python manage.py makemigrates
   - **Ejecutar migraciones:**
   - docker-compose exec web python manage.py migrate
   - **Recolectar archivos estáticos:**
   - docker-compose exec web python manage.py collectstatic --noinput
   - **Crear Super Usuario:**
   - docker-compose exec web python manage.py createsuperuser
7. Acceder a la Aplicación:
   - Abre tu navegador y dirígete a: http://kinelearn.ucn.cl/ o http://127.0.0.1
         - Nota: Si se quiere que http://kinelearn.ucn.cl funcione, se debe:
                 - Ir a tu Windows en archivos.
                 - Carpeta System32.
                 - Drivers.
                 - Carpeta “Etc”.
                 - Doc “HOSTS” .
                 - Abrirlo con visual studio.
                 - Agregar al final (antes de la última línea): 127.0.0.1 kinelearn.ucn.cl
                 - Guardar cambios (los más probable es que salte una alerta, debes presionar retry as admin).
                 - Cerrar y aceptar los cambios en el dispositivo.
8. Verificación:
   - Verificar que el proyecto y sus servicios (WEB y BD) aparezcan como activos en Docker Desktop.
 
### Opción 2: Instalación Local (Python/PostgreSQL)
- ***Requisitos: tener Python instalado y Postgresql***
1. Clonar el repositorio:
   - Descargar el repositorio (ya sea descargando el ZIP o clonando la URL).
2. Entrar al terminal
3. Crear y activar un entorno virtual:
   - Utilice el comando: python -m venv .entorno 
4. Crear dependencias, use librerías: django, psycopg2 y django-jazzmin.
5. Configurar PostgreSQL:
   - Crear la base de datos: CREATE DATABASE db_kinelearn;
   - Crear el usuario: CREATE USER user_admin;
   - Asignar contraseña al usuario: ALTER ROLE user_admin WITH PASSWORD '1234';
   - Conectar a la DB: \c db_kinelearn;
   5.6 Crear schemas y permisos: GRANT USAGE ON SCHEMA public TO user_admin; | GRANT CREATE ON SCHEMA public TO user_admin;
7. Migrar la base de datos en la terminal
   - 7.1 Utilice los siguientes comandos, uno a la vez:
   - python manage.py makemigrations
   - python manage.py migrate
8. Crear un superusuario y cargar los datos iniciales
   - python manage.py createsuperuser
9. Ejecutar el servidor
   - python manage.py runserver


## Datos de conexión de la base de datos
A continuación se muestran los parámetros de conexión utilizados por el proyecto **KineLearn**.  
*Los valores son de ejemplo y no representan credenciales reales.*
- **Tipo de base de datos:** PostgreSQL  
- **Host:** localhost  
- **Puerto:** 5432  
- **Nombre de la base de datos:** kinelearn_db  
- **Usuario:** kinelearn_user  
- **Contraseña:** ******** (no se expone públicamente)
