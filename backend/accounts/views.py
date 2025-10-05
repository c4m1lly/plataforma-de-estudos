from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login as dj_login, logout as dj_logout
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .permissions import IsAdminOrSelf
from .services import send_password_reset_email, verify_password_reset, set_new_password

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    /accounts/users/ [GET, POST]
    /accounts/users/{uuid}/ [GET, PATCH, DELETE]
    /accounts/users/register/ [POST]
    """
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create", "register"]:
            return [AllowAny()]
        if self.action in ["list", "destroy"]:
            return [IsAdminUser()]
        if self.action in ["partial_update", "update", "retrieve"]:
            return [IsAuthenticated(), IsAdminOrSelf()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # Session login (opcional)
        dj_login(request, user)
        # JWT tokens (SimpleJWT)
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Session logout
        dj_logout(request)
        # Optional blacklist for JWT refresh if sent
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # requires blacklisting app installed
            except Exception:
                pass
        return Response({"detail": "Logout realizado."}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"detail": "Senha atual incorreta."}, status=status.HTTP_400_BAD_REQUEST)
        new_password = serializer.validated_data["new_password"]
        set_new_password(user, new_password)
        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Não revelar se e-mail existe
            return Response({"detail": "Se o e-mail existir, enviaremos instruções."}, status=status.HTTP_200_OK)
        ok, msg = send_password_reset_email(user, request)
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
            return Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)
        set_new_password(user, serializer.validated_data["new_password"])
        return Response({"detail": "Senha redefinida com sucesso."})

class TokenRefresh(TokenRefreshView):
    permission_classes = [AllowAny]

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        from .serializers import UserSerializer
        return Response(UserSerializer(request.user).data)
