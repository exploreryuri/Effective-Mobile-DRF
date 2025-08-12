from rest_framework.permissions import BasePermission
from .utils import best_scope

def require_permission(resource: str, action: str):
    class _RequirePermission(BasePermission):
        def has_permission(self, request, view):
            scope = best_scope(request.user, resource, action)
            if not scope:
                return False  # DRF вернёт 403 для аутентифицированных
            request.rbac = {"resource": resource, "action": action, "scope": scope}
            return True
    return _RequirePermission
