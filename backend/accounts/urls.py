from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, LoginView, LogoutView, ChangePasswordView,
    ForgotPasswordView, ResetPasswordView, TokenRefresh, MeView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/refresh/", TokenRefresh.as_view(), name="token_refresh"),
    # compat: /accounts/users/update-user/<uuid>/ -> partial_update (PATCH)
    path("users/update-user/<uuid:pk>/", UserViewSet.as_view({"patch": "partial_update"}), name="update-user"),
]