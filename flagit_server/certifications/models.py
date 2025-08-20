from django.db import models
from django.contrib.gis.db.models import PointField
from django.contrib.gis.geos import Point
from django.conf import settings
from stores.models import Store

# Create your models here.
class Certification(models.Model):
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('completed', '완료'),
        ('expired', '만료')
    ]
    
    certification_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    lat = models.FloatField()
    lng = models.FloatField()
    location = PointField(null=True, blank=True)  # PostGIS PointField
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        # lat, lng로 Point 객체 생성
        if self.lat and self.lng:
            self.location = Point(self.lng, self.lat, srid=4326)  # WGS84 좌표계
        super().save(*args, **kwargs)
