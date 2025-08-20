from django.contrib.auth.models import AbstractUser
from django.db import models
from location.models import Location
from crew.models import CrewMember
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
    
class Badge(models.Model):
    badge_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.badge_name

class User(AbstractBaseUser, PermissionsMixin):
    nickname = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    profile_image = models.URLField(blank=True, null=True)
    flag_count = models.PositiveIntegerField(default=0)
    total_distance = models.FloatField(default=0.0)  # km 단위
    activities_count = models.PositiveIntegerField(default=0)
    discounts_count = models.PositiveIntegerField(default=0)

    badges = models.ManyToManyField(Badge, related_name='users')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'   # 로그인 필드 변경 (선택 사항)
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()

    def __str__(self):
        return self.email

class ActivityLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True, null=True)

    visited_at = models.DateTimeField(auto_now_add=True)

    location_lat = models.FloatField()
    location_lng = models.FloatField()

    def __str__(self):
        return f"{self.user.nickname} visited {self.name} on {self.visited_at.strftime('%Y-%m-%d')}"
    
class Flag(models.Model):
    ACTIVITY_TYPES = (
        ('running', '러닝'),
        ('hiking', '등산'),
        ('riding', '라이딩'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="personal_flags"
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='flags'
    )

    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    date = models.DateField()
    distance_km = models.FloatField()
    time_record = models.DurationField()  # 시:분:초 형태 저장
    crew_members = models.ManyToManyField(
        CrewMember, blank=True, null=True, related_name='joined_flags'
    )

    group_photo = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
