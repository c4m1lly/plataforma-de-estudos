from typing import Optional, Tuple
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail as django_send_mail
from .models import User

try:
    from services.email_service import send_mail as project_send_mail  # opcional no seu projeto
except Exception:
    project_send_mail = None

token_generator = PasswordResetTokenGenerator()

def build_password_reset_link(user: User, request) -> str:
    uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
    token = token_generator.make_token(user)
    base = getattr(settings, "FRONTEND_URL", None)
    if base:
        # exemplo: {FRONTEND_URL}/reset?uid=...&token=...
        return f"{base.rstrip('/')}/reset-password?uid={uid}&token={token}"
    # fallback: API endpoint
    scheme = "https" if request.is_secure() else "http"
    host = request.get_host()
    return f"{scheme}://{host}/accounts/auth/reset-password/?uid={uid}&token={token}"

def send_password_reset_email(user: User, request) -> Tuple[bool, str]:
    subject = "Redefinição de senha"
    reset_link = build_password_reset_link(user, request)
    body = (
        "Você solicitou a redefinição de senha.\n\n"
        f"Clique no link para continuar: {reset_link}\n\n"
        "Se você não solicitou, ignore este e-mail."
    )
    try:
        if project_send_mail:
            project_send_mail(subject, body, to=[user.email])
        else:
            django_send_mail(
                subject=subject,
                message=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True, "E-mail de redefinição enviado."
    except Exception as e:
        return False, str(e)

def verify_password_reset(uidb64: str, token: str) -> Optional[User]:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        return None
    if token_generator.check_token(user, token):
        return user
    return None

def set_new_password(user: User, new_password: str):
    user.set_password(new_password)
    user.last_password_reset = timezone.now()
    user.save(update_fields=["password", "last_password_reset"])