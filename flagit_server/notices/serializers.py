from rest_framework import serializers
from notices.models import Notice, NoticeReaction

class NoticeSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    
    class Meta:
        model = Notice
        fields = '__all__'

class NoticeReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeReaction
        fields = '__all__'