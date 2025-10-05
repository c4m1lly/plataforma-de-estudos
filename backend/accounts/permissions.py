from rest_framework.permissions import BasePermission

class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user and (request.user.is_staff or request.user == obj)