from datetime import timedelta

INSTALLED_APPS = [
    # Django apps nativos...
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceiros
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",  # opcional, mas útil p/ logout com blacklist

    # Apps locais
    "accounts",
    "learning",
    "courses",
    "quizzes",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

CORS_ALLOW_ALL_ORIGINS = True  # em dev/local

# E-mail em DEV: imprime no terminal
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@local.test"

# Arquivos de mídia (p/ upload de vídeos no learning)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATIC_URL = "/static/"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,  # se estiver usando token_blacklist
    "AUTH_HEADER_TYPES": ("Bearer",),

    # >>> Ajustes para User com UUID <<<
    "USER_ID_FIELD": "uuid",     # <- seu PK
    "USER_ID_CLAIM": "user_id",  # nome do claim no token (pode manter "user_id")
}
YOUTUBE_API_KEY = "AIzaSyCcOtrjqrB4SCsOF5vpofATfLmXLg2HDjA"
