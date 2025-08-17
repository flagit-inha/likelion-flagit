from rest_framework import serializers
from .models import Certification

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['lat', 'lng']

    def create(self, validated_data):
        member = self.context['request'].user
        store = self.context['request'].store
        validated_data['member'] = member
        validated_data['store'] = store
        validated_data['status'] = 'pending'
        return super().create(validated_data)

