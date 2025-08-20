from rest_framework import serializers
from .models import Route

class RouteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Route
        fields = [
            'route_id', 
            'crew_member', 
            'start_lat', 
            'start_lng', 
            'target_distance', 
            'route_path'
        ]
        read_only_fields = ['route_id']

class RouteRecommendationRequestSerializer(serializers.Serializer):
    start_lat = serializers.FloatField()
    start_lng = serializers.FloatField()
    target_distance = serializers.FloatField()

class RouteRecommendationResponseSerializer(serializers.Serializer):
    route_id = serializers.IntegerField(required=False, allow_null=True)
    route_path = serializers.ListField(
        child=serializers.DictField(),
    )

class RouteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            'crew_member', 
            'start_lat', 
            'start_lng', 
            'target_distance', 
            'route_path'
        ]
    
    def validate_route_path(self, value):
        """route_path 필드 검증"""
        if not isinstance(value, list):
            raise serializers.ValidationError("route_path는 리스트 형태여야 합니다.")
        
        for i, point in enumerate(value):
            if not isinstance(point, dict):
                raise serializers.ValidationError(f"지점 {i}는 딕셔너리 형태여야 합니다.")
            
            if 'lat' not in point or 'lng' not in point:
                raise serializers.ValidationError(f"지점 {i}에 lat과 lng가 필요합니다.")
            
            try:
                lat = float(point['lat'])
                lng = float(point['lng'])
                    
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"지점 {i}의 lat과 lng는 숫자여야 합니다.")
        
        return value
