"""
URL configuration for authsys project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from rest_framework.routers import DefaultRouter

from accounts.views import RegisterView, LoginView, RefreshView, LogoutView, MeView
from mockapp.views import ArticleList, ArticleUpdate
from rbac.views import PermissionViewSet, RolePermissionViewSet, RoleViewSet, UserRoleViewSet

router = DefaultRouter()
router.register(r"rbac/roles", RoleViewSet, basename="rbac-roles")
router.register(r"rbac/permissions", PermissionViewSet, basename="rbac-perms")
router.register(r"rbac/role-permissions", RolePermissionViewSet, basename="rbac-role-perms")
router.register(r"rbac/user-roles", UserRoleViewSet, basename="rbac-user-roles")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", RefreshView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("users/me/", MeView.as_view()),
    path("articles/", ArticleList.as_view()),
    path("articles/<int:article_id>/", ArticleUpdate.as_view()),
]

urlpatterns += router.urls
