from django.utils import timezone
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from .serializers import RegisterSerializer, LoginSerializer, MeUpdateSerializer
from .jwt import create_access_token, create_refresh_token, decode_token
from .models import RefreshToken

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"id": user.id, "email": user.email}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(request, username=ser.validated_data["email"], password=ser.validated_data["password"])
        if not user or not user.is_active:
            return Response({"detail":"Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        access = create_access_token(user.id)
        refresh, jti, exp = create_refresh_token(user.id)
        RefreshToken.objects.create(user=user, jti=jti, expires_at=exp,
                                    user_agent=request.META.get("HTTP_USER_AGENT",""),
                                    ip=request.META.get("REMOTE_ADDR"))

        return Response({"access": access, "refresh": refresh})

class RefreshView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail":"Refresh token required"}, status=400)
        try:
            payload = decode_token(token, expected_typ="refresh")
        except ValueError as e:
            return Response({"detail": str(e)}, status=401)

        user_id = int(payload["sub"])
        jti = payload["jti"]
        try:
            rt = RefreshToken.objects.get(user_id=user_id, jti=jti)
        except RefreshToken.DoesNotExist:
            return Response({"detail":"Refresh not found"}, status=401)
        if not rt.is_active:
            return Response({"detail":"Refresh revoked or expired"}, status=401)

        # Ротация refresh: старый отзываем, выдаём новый
        rt.revoked_at = timezone.now()
        rt.save(update_fields=["revoked_at"])

        new_refresh, new_jti, new_exp = create_refresh_token(user_id)
        RefreshToken.objects.create(user_id=user_id, jti=new_jti, expires_at=new_exp,
                                    user_agent=request.META.get("HTTP_USER_AGENT",""),
                                    ip=request.META.get("REMOTE_ADDR"))
        new_access = create_access_token(user_id)
        return Response({"access": new_access, "refresh": new_refresh})

class LogoutView(APIView):
    def post(self, request):
        # Отзываем все активные refresh для пользователя (глобальный logout)
        qs = RefreshToken.objects.filter(user=request.user, revoked_at__isnull=True, expires_at__gt=timezone.now())
        qs.update(revoked_at=timezone.now())
        return Response(status=204)

class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({
            "id": u.id, "email": u.email,
            "first_name": u.first_name, "last_name": u.last_name, "patronymic": u.patronymic
        })

    def patch(self, request):
        ser = MeUpdateSerializer(instance=request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def delete(self, request):
        request.user.soft_delete()
        RefreshToken.objects.filter(user=request.user, revoked_at__isnull=True).update(revoked_at=timezone.now())
        return Response(status=204)
