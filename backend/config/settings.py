"""
Django settings for config project.
Panadería Santiago (SI-1)
"""
from decouple import config
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-yot6^&k^j2mt*-6gc%6-fh%&d0i&4=+z48v5i5v$w+5mfeoui&')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    # Necesario para que BLACKLIST_AFTER_ROTATION tenga efecto: sin esta app el
    # ajuste de SimpleJWT es inerte y los refresh tokens nunca se revocan.
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    # Paquete 1: Usuarios y Seguridad (Sub-apps modulares)
    'apps.usuarios_seguridad.permisos',
    'apps.usuarios_seguridad.roles',
    'apps.usuarios_seguridad.users',
    'apps.usuarios_seguridad.bitacora',
    'apps.usuarios_seguridad.configuracion',
    'apps.usuarios_seguridad.recuperacion',
    'apps.usuarios_seguridad.auth_app',

    # Paquetes restantes
    'apps.productos_inventario',
    'apps.compras',
    'apps.comercializacion',
    'apps.reportes',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='panaderia_santiago_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Modelo de Usuario personalizado para Panadería Santiago
AUTH_USER_MODEL = 'users.Usuario'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'apps.usuarios_seguridad.users.password_validators.ComplexPasswordValidator',
        'OPTIONS': {'min_length': 8},
    },
]


# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Frecuencia de los límites anti-abuso, en formato 'nº de peticiones / ventana'.
    # Son Django Throttles y solo afectan a las vistas que los activen. El límite
    # por cuenta vive en la tabla `configuracion_seguridad`, y el de intentos por
    # enlace de recuperación, en la fila `token_recuperacion`: son tres capas
    # distintas que no se sustituyen entre sí.
    # OJO: debe ir DENTRO de REST_FRAMEWORK; una clave suelta de primer nivel
    # sería ignorada silenciosamente por DRF.
    'DEFAULT_THROTTLE_RATES': {
        'login': '10/min',
        'refresh': '30/min',
        # CU2. Pedir un enlace es más caro de enviar que pedir un token de
        # sesión, y además genera correo: por eso es más restrictivo que el
        # login. Confirmar es más laxo porque el solicitante ya trae un token
        # secreto en la URL, y el límite real ahí lo pone el contador de
        # intentos de esa misma fila.
        'password_reset_request': '5/min',
        'password_reset_confirm': '15/min',
    },
}

# SimpleJWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    # Cada refresh entrega un token nuevo y manda el anterior a la lista negra.
    # Requiere la app 'rest_framework_token_blacklist' en INSTALLED_APPS.
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id_usuario',
    'USER_ID_CLAIM': 'id_usuario',
}


# Internationalization
LANGUAGE_CODE = 'es-bo'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True


# ==================================================================
# Envío de correo (CU2 — Recuperar contraseña)
# ==================================================================
# Django SIEMPRE habla SMTP. Lo único que cambia es a qué servidor apunta, y eso
# se decide acá con `EMAIL_BACKEND`. Por eso no hay una decisión de arquitectura
# entre "correo de prueba" y "correo real": hay una sola variable y dos valores.
#
#   Desarrollo  -> .env pone el backend smtp contra localhost:1025 (Mailpit)
#                  y el correo se lee en http://localhost:8025
#   Producción  -> .env apunta al SMTP del proveedor real
#
# El valor por defecto es el backend de consola: sin ninguna variable en el .env
# el sistema sigue funcionando, escribiendo el correo en la terminal. Es
# deliberado que ese sea el default y no el de producción: un despliegue
# olvidado no debe dejar de enviar correos en silencio.
#
# Mailpit se instala FUERA de Python (binario de Windows, o scoop/winget). No es
# una dependencia del proyecto, así que no va en requirements.txt.
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
# Corta el envío en vez de dejar la petición colgada si el servidor no responde.
# Sin esto, un SMTP caído bloquea el hilo de la vista durante el timeout del
# socket y el usuario ve la pantalla congelada.
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='no-reply@panaderiasantiago.com',
)

# Ruta del FRONTEND donde el usuario escribe la contraseña nueva. El backend no
# tiene ninguna vista de recuperación: envía un enlace a la SPA, que es la que
# muestra el formulario y consume POST /api/auth/password-reset-confirm/. Es la
# misma división de responsabilidades que en el CU1, donde React es el cliente y
# Django la API.
PASSWORD_RESET_URL = config(
    'PASSWORD_RESET_URL',
    default='http://localhost:5173/recuperar-password/nueva',
)