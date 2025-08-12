from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated

class RequireAuthenticated401(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication credentials were not provided.")
        return True
