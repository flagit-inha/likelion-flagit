from django.db import models
from django.conf import settings
import uuid

class Crew(models.Model):
    CREW_TYPES = (
        ('running', '러닝'),
        ('hiking', '등산'),
        ('riding', '라이딩'),
    )

    crew_id = models.AutoField(primary_key=True)
    leader_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='led_crews')
    crewname = models.CharField(max_length=100)
    invitecode = models.CharField(max_length=20, unique=True, default=uuid.uuid4().hex[:8])
    type = models.CharField(max_length=10, choices=CREW_TYPES)
    member_count = models.PositiveIntegerField(default=1)
    logo = models.ImageField(upload_to='crew_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.crewname} ({self.get_type_display()})"
    
class CrewMember(models.Model):
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crew_memberships')

    class Meta:
        # 한 명의 유저가 한 크루에 여러 번 가입할 수 없도록 고유성 제약조건 추가
        unique_together = ('crew', 'user')