from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login as dj_login, logout as dj_logout
from django.utils import timezone

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .permissions import IsAdminOrSelf
from .services import (
    send_password_reset_email, verify_password_reset, set_new_password
)


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários.
    - Admin pode listar todos e editar qualquer um.
    - Usuário comum só pode ver/editar a si mesmo.
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create", "register"]:
            return [AllowAny()]
        if self.action in ["list", "destroy", "partial_update", "update"]:
            # list/destroy exigem admin; update parcial pode ser self ou admin
            if self.action == "list" or self.action == "destroy":
                return [IsAdminUser()]
            return [IsAuthenticated(), IsAdminOrSelf()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # opcional: login de sessão (se quiser usar SessionAuthentication)
        dj_login(request, user)

        # JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Se usar JWT com blacklist, invalida o refresh recebido
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass
        dj_logout(request)
        return Response({"detail": "Logout realizado."}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Senha atual incorreta."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.last_password_reset = timezone.now()
        user.save(update_fields=["password", "last_password_reset"])
        return Response({"detail": "Senha alterada com sucesso."})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Não revele existência — responda sucesso mesmo assim
            return Response({"detail": "Se o e-mail existir, enviaremos instruções."})
        ok, msg = send_password_reset_email(user)
        status_code = status.HTTP_200_OK if ok else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response({"detail": msg}, status=status_code)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        user = verify_password_reset(uid, token)
        if not user:
            return Response({"detail": "Token inválido ou expirado."},
                            status=status.HTTP_400_BAD_REQUEST)
        set_new_password(user, serializer.validated_data["new_password"])
        return Response({"detail": "Senha redefinida com sucesso."})


# Reuso do endpoint de refresh padrão do SimpleJWT:
class TokenRefresh(TokenRefreshView):
    permission_classes = [AllowAny]
