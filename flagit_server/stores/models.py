from django.db import models

# Create your models here.
class Store(models.Model):
    store_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    lat = models.FloatField() # 위도
    lng = models.FloatField() # 경도
    location = models.PointField() # 위치
    required_count = models.IntegerField()
