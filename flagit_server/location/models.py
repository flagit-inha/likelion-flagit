# location/models.py
from django.db import models
from django.contrib.gis.db import models as gis_models

class Location(models.Model):
    name = models.CharField(max_length=255)
    location_distance = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.name