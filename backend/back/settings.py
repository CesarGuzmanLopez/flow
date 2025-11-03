"""
Configuración de Django para el proyecto ChemFlow.

Generado por 'django-admin startproject' usando Django 5.2.7.

Este archivo contiene toda la configuración del backend incluyendo:
- Configuración de base de datos
- Aplicaciones instaladas (Django REST Framework, SimpleJWT, etc.)
- Middleware y seguridad
- Configuración de autenticación JWT
- Configuración de OpenAPI/Swagger con drf-spectacular
- CORS para desarrollo frontend

Para más información sobre este archivo, ver:
https://docs.djangoproject.com/en/5.2/topics/settings/

Para la lista completa de configuraciones y sus valores, ver:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()
# Default chemistry engine to RDKit if not explicitly set in environment.
# This ensures management commands and migrations use RDKit by default.
os.environ.setdefault("CHEM_ENGINE", "rdkit")
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-q$(5w%1&(1!&*o1&q($ohdts9v1$@*^o6jvuc26w*apxb^-f^c",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.getenv("DJANGO_ALLOWED_HOSTS")
    else []
)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "users",
    "flows",
    "chemistry",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Wrap JSON responses in standard envelope across the API
    "back.middleware.StandardResponseEnvelopeMiddleware",
]

ROOT_URLCONF = "back.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "back" / "templates"],
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

WSGI_APPLICATION = "back.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# If you later provide a DATABASE_URL in the environment, you can switch to Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    # Defer to dj-database-url or manual parsing if you decide to enable Postgres later.
    # For now we keep sqlite as default for easy local development.
    pass

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Global renderer to wrap responses in the standard envelope
    "DEFAULT_RENDERER_CLASSES": (
        "back.renderers.StandardJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    # Normalize error responses
    "EXCEPTION_HANDLER": "back.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "🧪 ChemFlow API",
    "DESCRIPTION": """
        ## Molecular Chemistry & Flow Management API
        
        ChemFlow provides a comprehensive RESTful API for:
        
        - **Molecular Management**: Create, retrieve, update molecules with SMILES/InChI formats
        - **Property Calculations**: Generate chemical properties (ADMETSA, descriptors) via multiple providers
        - **Family Organization**: Group molecules into families with aggregate statistics
        - **Flow Processing**: Execute computational chemistry workflows
        - **User Management**: Authentication, authorization, and team collaboration
        
        ### Key Features
        
        - 🔬 Multiple property generation providers (RDKit, Manual, Ollama)
        - 📊 Statistical aggregation for molecular families
        - 🔐 JWT-based authentication with role-based permissions
        - 📡 Real-time updates via WebSockets
        - 🧬 Support for standard chemistry formats (SMILES, InChI, Mol2, PDB)
        
        ### Getting Started
        
        1. Authenticate via `/api/users/token/` to get JWT tokens
        2. Include `Authorization: Bearer <token>` header in requests
        3. Explore endpoints for molecules, families, properties, and flows
        
        For detailed examples and integration guides, see the [GitHub repository](https://github.com/CesarGuzmanLopez/flow).
    """,
    "VERSION": "1.0.0",
    "CONTACT": {
        "name": "ChemFlow Development Team",
        "url": "https://github.com/CesarGuzmanLopez/flow",
    },
    "LICENSE": {
        "name": "MIT License",
        "url": "https://github.com/CesarGuzmanLopez/flow/blob/master/LICENSE",
    },
    "EXTERNAL_DOCS": {
        "description": "ChemFlow Documentation & Examples",
        "url": "https://github.com/CesarGuzmanLopez/flow/blob/master/README.md",
    },
    "TAGS": [
        {"name": "chemistry", "description": "🧪 Molecular chemistry endpoints"},
        {"name": "flows", "description": "🌊 Workflow and flow management"},
        {"name": "users", "description": "👤 User authentication and management"},
        {"name": "notifications", "description": "🔔 Notification system"},
    ],
    "POSTPROCESSING_HOOKS": [
        "back.spectacular_overrides.fix_add_property_schema",
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "docExpansion": "none",  # Contraer todo por defecto
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
    # Security schemes for JWT authentication
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "JWT authentication using access tokens. "
                    "Login via the 🔒 button in the header or use the "
                    "`/api/token/` endpoint to obtain a token."
                ),
            }
        }
    },
    "SECURITY": [{"jwtAuth": []}],
    # Use custom template with download buttons and chemistry theme
    "SWAGGER_UI_DIST": "https://unpkg.com/swagger-ui-dist@5",
    "SWAGGER_UI_FAVICON_HREF": (
        "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' "
        "viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧪</text></svg>"
    ),
}

# Custom user model
AUTH_USER_MODEL = "users.User"

# SimpleJWT Settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Persist a signing key for JWT so tokens survive server restarts.
# By default DRF SimpleJWT will use SECRET_KEY for HS256, but some
# deployments generate SECRET_KEY at runtime or use ephemeral containers.
# We store a dedicated signing secret in a file inside the project base
# directory (only when running locally). In production you should provide
# a stable secret via environment variable `JWT_SIGNING_KEY` or mount a
# secret file into the container.
JWT_SIGNING_KEY_FILE = BASE_DIR / ".jwt_signing_key"
_jwt_key = os.getenv("JWT_SIGNING_KEY")
if not _jwt_key:
    try:
        if JWT_SIGNING_KEY_FILE.exists():
            _jwt_key = JWT_SIGNING_KEY_FILE.read_text(encoding="utf-8").strip()
        else:
            # generate a random key and persist it with restrictive permissions
            _jwt_key = os.urandom(64).hex()
            with open(JWT_SIGNING_KEY_FILE, "w", encoding="utf-8") as f:
                f.write(_jwt_key)
            try:
                # Try to restrict file permissions (POSIX)
                os.chmod(JWT_SIGNING_KEY_FILE, 0o600)
            except Exception:
                # Best-effort only; some filesystems may not support chmod
                pass
    except Exception:
        # Fallback to Django SECRET_KEY if file cannot be used for any reason
        _jwt_key = SECRET_KEY

# Configure SimpleJWT to use the persistent signing key
SIMPLE_JWT["SIGNING_KEY"] = _jwt_key

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

LANGUAGE_CODE = "es-MX"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS para desarrollo (Angular en localhost)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# Email Configuration
# En desarrollo, los emails se muestran en consola
# En producción, configurar SMTP real
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",  # Desarrollo: imprime en consola
)

# Configuración SMTP para producción (vía variables de entorno)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@chemflow.com")

# URL del frontend para enlaces en emails
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

# External tools configuration (AMBIT-SA Java provider)
# You can override these via environment variables or a .env file.
# If not provided, we default to the expected locations inside the repo.
AMBIT_JAR_PATH = os.getenv(
    "AMBIT_JAR_PATH",
    str(BASE_DIR / "tools" / "external" / "ambitSA" / "SyntheticAccessibilityCli.jar"),
)
AMBIT_JAVA_PATH = os.getenv(
    "AMBIT_JAVA_PATH",
    str(BASE_DIR / "tools" / "java" / "jre8" / "bin" / "java"),
)
