from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from django.contrib.auth import get_user_model
from .jwt import decode_token

User = get_user_model()

class JWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate_header(self, request):
        # Подсказываем DRF схему — тогда при отсутствии токена будет 401 + WWW-Authenticate
        return "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth:
            return None
        if auth[0].lower() != self.keyword or len(auth) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header")
        token = auth[1].decode("utf-8")

        try:
            payload = decode_token(token, expected_typ="access")
        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e))

        user_id = int(payload.get("sub"))
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found or inactive")
        return (user, payload)
