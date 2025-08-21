from rest_framework import serializers
from .models import Store
from django.contrib.gis.geos import Point

class StoreSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)  
    lng = serializers.FloatField(write_only=True) 
    
    class Meta:
        model = Store
        fields = ['store_id', 'name', 'lat', 'lng', 'required_count']
    
    def create(self, validated_data):
        # lat, lng을 location으로 변환
        lat = validated_data.pop('lat')
        lng = validated_data.pop('lng')
        
        # Point 객체 생성
        location = Point(x=lng, y=lat, srid=4326)
        
        # 가게 생성
        store = Store.objects.create(
            lat=lat,
            lng=lng,
            location=location,
            **validated_data
        )
        
        return store

class StoreListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['store_id', 'name', 'lat', 'lng', 'required_count']