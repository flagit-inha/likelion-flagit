# location/models.py
from django.db import models
from django.contrib.gis.db import models as gis_models

class Location(models.Model):
    name = models.CharField(max_length=255)
    location_lat = models.FloatField()
    location_lng = models.FloatField()  
    
    def __str__(self):
        return self.name