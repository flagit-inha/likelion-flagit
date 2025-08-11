from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser

class UserManager(BaseUserManager):
    def create_user(self, email, nickname, password=None):
        if not email:
            raise ValueError("이메일을 반드시 입력해야 합니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, nickname=nickname)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password=None):
        user = self.create_user(email=email, nickname=nickname, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    nickname = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    profile_image = models.URLField(blank=True, null=True)
    flag_count = models.PositiveIntegerField(default=0)
    total_distance = models.FloatField(default=0.0)  # km 단위

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'   # 로그인 필드 변경 (선택 사항)
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()

    def __str__(self):
        return self.email
