from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsCourseOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "owner", None)
        if request.method in SAFE_METHODS:
            return True if owner is None else (request.user and (request.user == owner or request.user.is_staff))
        return request.user and (request.user == owner or request.user.is_staff)