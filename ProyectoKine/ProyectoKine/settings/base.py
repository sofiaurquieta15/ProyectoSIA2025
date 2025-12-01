from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ok8b9@mu3@eumbb1#8gkz+8b5r(rs#6^ym%p%gi-up67cukwf_"


# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    #aplicaciones propias
    "applications.login",
    "applications.cursosestudiante",
    "applications.cursosdocente",
    "applications.casospacientes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ProyectoKine.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ProyectoKine.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "es-es"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

JAZZMIN_SETTINGS={
    "site_title": "KineLearn Admin",
    "site_header": "KineLearn Dashboard",
    "welcome_sign": "Bienvenido a KineLearn",
    "site_brand": "KineLearn",
    "site_logo": "images/logo_UCN.png",
    "site_icon": "images/logo_UCN.png",
    "custom_css": "css/admin_custom.css",
    "custom_js": None,

    "icons": {
        # === APP login ===
        "login.docente": "fas fa-chalkboard-teacher",
        "login.estudiante": "fas fa-user-graduate",

        # === APP cursosdocente ===
        "cursosdocente.curso": "fas fa-book",

        # === APP casospacientes (tus modelos de casos/pacientes/etapas/preguntas/etc.) ===
        "casospacientes.etapacompletada":"fas fa-check-circle",
        "casospacientes.tipocaso": "fas fa-tags",
        "casospacientes.paciente": "fas fa-user-injured",
        "casospacientes.etapa": "fas fa-layer-group",
        "casospacientes.pregunta": "fas fa-question-circle",
        "casospacientes.opcionmultiple": "fas fa-check-square",
        "casospacientes.registro": "fas fa-clipboard-check",
        "casospacientes.exploracion":"fas fa-search-plus",

        # === APP cursosestudiante ===
        "cursosestudiante.avance": "fas fa-tasks",
        "cursosestudiante.enrolamiento": "fas fa-user-plus",

        # === Django interno ===
        "auth.user": "fas fa-user-cog",
        "auth.group": "fas fa-users-cog",
    },

    "order_with_respect_to": [

        # Bloque 1: Login
        "login.docente",
        "login.estudiante",

        # Bloque 2: CursosDocente
        "cursosdocente.curso",

        # Bloque 3: CasosPacientes
        "casospacientes.tipocaso",
        "casospacientes.paciente",
        "casospacientes.etapa",
        "casospacientes.pregunta",
        "casospacientes.exploracion",
        "casospacientes.opcionmultiple",
        "casospacientes.registro",
        "casospacientes.etapacompletada",

        # Bloque 4: CursosEstudiante
        "cursosestudiante.enrolamiento",
        "cursosestudiante.avance",

        # Bloque 4: autenticación
        "auth",
    ]
}
