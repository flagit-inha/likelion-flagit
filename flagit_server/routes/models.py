from django.db import models
from crew.models import CrewMember, Crew

# Create your models here.
class Route(models.Model):
    route_id = models.AutoField(primary_key=True)
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE)
    crew_type = models.CharField(max_length=10, choices=Crew.CREW_TYPES)
    start_location = models.CharField(max_length=255) # 출발 경도, 위도 형식에서 -> 출발 위치로 변경
    target_distance = models.FloatField()
    route_path = models.JSONField(default=list)  # 경로상의 모든 위치를 저장