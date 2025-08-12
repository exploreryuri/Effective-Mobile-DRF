from rest_framework.viewsets import ModelViewSet
from rbac.permissions import require_permission
from rbac.auth_required import RequireAuthenticated401
from .models import Role, Permission, RolePermission, UserRole
from .serializers import (
    RoleSerializer, PermissionSerializer, RolePermissionSerializer, UserRoleSerializer
)

class RBACBaseViewSet(ModelViewSet):
    permission_classes = [RequireAuthenticated401, require_permission("rbac", "manage")]

class RoleViewSet(RBACBaseViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer

class PermissionViewSet(RBACBaseViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

class RolePermissionViewSet(RBACBaseViewSet):
    queryset = RolePermission.objects.select_related("role", "permission").all()
    serializer_class = RolePermissionSerializer

class UserRoleViewSet(RBACBaseViewSet):
    queryset = UserRole.objects.select_related("user", "role").all()
    serializer_class = UserRoleSerializer
