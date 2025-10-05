
from dataclasses import dataclass
from typing import Optional, Tuple
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.conf import settings
from .models import User

try:
    from services.email_service import send_mail as project_send_mail
except Exception:
    project_send_mail = None


token_generator = PasswordResetTokenGenerator()


@dataclass
class PasswordResetPayload:
    uid: str
    token: str
    email: str


def build_frontend_reset_url(uid: str, token: str) -> str:
    """
    Monte aqui a URL do seu front-end. Exemplo:
    https://app.seudominio.com/reset-password?uid=...&token=...
    """
    base = getattr(settings, "FRONTEND_RESET_PASSWORD_URL",
                   "https://example.com/reset-password")
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}uid={uid}&token={token}"


def create_password_reset_payload(user: User) -> PasswordResetPayload:
    uid = urlsafe_base64_encode(force_bytes(str(user.uuid)))
    token = token_generator.make_token(user)
    return PasswordResetPayload(uid=uid, token=token, email=user.email)


def verify_password_reset(uid: str, token: str) -> Optional[User]:
    try:
        uuid_str = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(uuid=uuid_str)
    except Exception:
        return None
    if token_generator.check_token(user, token):
        return user
    return None


def send_password_reset_email(user: User) -> Tuple[bool, str]:
    payload = create_password_reset_payload(user)
    reset_link = build_frontend_reset_url(payload.uid, payload.token)
    subject = "Redefinição de senha"
    body = (
        f"Olá,\n\nRecebemos uma solicitação para redefinir sua senha.\n"
        f"Clique no link para continuar: {reset_link}\n\n"
        f"Se você não solicitou, ignore este e-mail."
    )

    # Preferir serviço do projeto se disponível
    if project_send_mail:
        try:
            project_send_mail(
                subject=subject,
                message=body,
                recipient_list=[user.email],
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            )
            return True, "E-mail de redefinição enviado."
        except Exception as e:
            return False, str(e)

    # Fallback: usar Django send_mail
    from django.core.mail import send_mail
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True, "E-mail de redefinição enviado."
    except Exception as e:
        return False, str(e)


def set_new_password(user: User, new_password: str):
    user.set_password(new_password)
    user.last_password_reset = timezone.now()
    user.save(update_fields=["password", "last_password_reset"])
