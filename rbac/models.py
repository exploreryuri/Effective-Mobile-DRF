from django.db import models
from django.conf import settings

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)          # admin, editor, viewer
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class Permission(models.Model):
    class Scope(models.TextChoices):
        ALL = "ALL", "ALL"
        OWN = "OWN", "OWN"

    resource = models.CharField(max_length=50)                   # articles, users, etc.
    action   = models.CharField(max_length=20)                   # read|create|update|delete
    scope    = models.CharField(max_length=3, choices=Scope.choices, default=Scope.ALL)

    class Meta:
        unique_together = ("resource", "action", "scope")

    def __str__(self):
        return f"{self.resource}:{self.action}:{self.scope}"

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role} -> {self.permission}"

class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_users")

    class Meta:
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user_id} -> {self.role}"
