# Accounts App (Custom User + Auth API)

Este módulo fornece:
- Modelo de usuário customizado com `email` como login.
- Endpoints REST (DRF + SimpleJWT) para **register**, **login**, **logout**, **refresh**, **change password**, **forgot/reset password**.
- Permissão `IsAdminOrSelf` para permitir PATCH do próprio usuário.

## Instalação

1. **INSTALLED_APPS** (settings.py):
```python
INSTALLED_APPS = [
    # ...
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # opcional para blacklist de refresh
    "accounts",
]
```

2. **User model** (settings.py):
```python
AUTH_USER_MODEL = "accounts.User"
DEFAULT_FROM_EMAIL = "no-reply@seuprojeto.com"
# (Opcional) para link no e-mail apontar pro seu front:
# FRONTEND_URL = "https://app.seuprojeto.com"
```

3. **REST Framework** (settings.py):
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}
```

4. **URLs do projeto** (urls.py do projeto):
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("accounts/", include("accounts.urls")),
]
```

5. **Migrations**:
```
python manage.py makemigrations accounts
python manage.py migrate
```

6. **Criar superusuário**:
```
python manage.py createsuperuser --email admin@exemplo.com
```

## Endpoints

- `POST /accounts/users/register/` { email, full_name, password }
- `POST /accounts/auth/login/` { email, password } -> { user, access, refresh }
- `POST /accounts/auth/logout/` { refresh? } (opcional para blacklist)
- `POST /accounts/auth/refresh/` { refresh }
- `POST /accounts/auth/change-password/` { old_password, new_password } (autenticado)
- `POST /accounts/auth/forgot-password/` { email }
- `POST /accounts/auth/reset-password/` { uid, token, new_password }
- `PATCH /accounts/users/update-user/<uuid>/` { ...campos... } (self/admin)

> Obs.: Para blacklist do refresh é necessário adicionar `rest_framework_simplejwt.token_blacklist` ao `INSTALLED_APPS` e configurar as migrations.

## Observações de e-mail
O serviço tenta usar `services.email_service.send_mail` do seu projeto se existir. Caso contrário, usa `django.core.mail.send_mail`. Configure `EMAIL_*` no `settings.py`.