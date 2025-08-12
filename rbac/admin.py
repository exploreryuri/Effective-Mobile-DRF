from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "resource", "action", "scope")
    list_filter = ("resource", "action", "scope")
    search_fields = ("resource", "action")

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("id", "role", "permission")
    list_filter = ("role",)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role")
    list_filter = ("role",)
    search_fields = ("user__email",)
