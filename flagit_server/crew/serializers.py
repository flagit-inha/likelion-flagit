import random
import string
from rest_framework import serializers
from .models import Crew
from .models import CrewMember

class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ('crewname', 'crew_type', 'invitecode')

    def validate_crewname(self, value):
        if Crew.objects.filter(crewname=value).exists():
            raise serializers.ValidationError("이미 존재하는 크루명입니다.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user  # 요청한 유저 (리더)
        
        # 초대코드 생성 (예: 8자리 랜덤 문자열)
        invitecode = validated_data.get('invitecode')
        if not invitecode:
            raise serializers.ValidationError("초대코드가 필요합니다.")
        
        crew = Crew.objects.create(
            leader=user,
            crewname=validated_data['crewname'],
            crew_type=validated_data['crew_type'],
            invitecode=invitecode,
            member_count=1,
        )
        CrewMember.objects.create(crew=crew, user=user)
        return crew
    
class CrewDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ('crew_id', 'crewname', 'crew_type', 'invitecode', 'member_count')