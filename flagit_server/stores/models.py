from django.db import models
from django.contrib.gis.db.models import PointField

# Create your models here.
class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    lat = models.FloatField() # 위도
    lng = models.FloatField() # 경도
    location = PointField() # 위치
    required_count = models.IntegerField()
    required_count = models.IntegerField(default=10)
    success_window_started_at = models.DateTimeField(null=True, blank=True)
    success_window_seconds = models.IntegerField(default=5)

