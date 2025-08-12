from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
import uuid
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self.create_user(email, password, **extra)
    
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name  = models.CharField(max_length=100, blank=True)
    patronymic = models.CharField(max_length=100, blank=True)

    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active","deleted_at"])


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="refresh_tokens")
    jti = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)  # идентификатор токена внутри JWT
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    @property
    def is_active(self):
        from django.utils import timezone
        return self.revoked_at is None and self.expires_at > timezone.now()