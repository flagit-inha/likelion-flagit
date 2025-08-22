from rest_framework import serializers
from .models import Certification

class CertificationSerializer(serializers.ModelSerializer):
    certification_id = serializers.IntegerField(read_only=True)
    member = serializers.PrimaryKeyRelatedField(read_only=True)
    store = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Certification
        fields = ['certification_id', 'lat', 'lng', 'member', 'store', 'status']

    def create(self, validated_data):
        member = self.context['request'].user
        store = self.context['store']
        validated_data['member'] = member
        validated_data['store'] = store
        validated_data['status'] = 'pending'
        return super().create(validated_data)

