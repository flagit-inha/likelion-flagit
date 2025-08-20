import random
import string
from rest_framework import serializers
from .models import Crew
from .models import CrewMember

class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ('crewname', 'type')

    def validate_crewname(self, value):
        if Crew.objects.filter(crewname=value).exists():
            raise serializers.ValidationError("이미 존재하는 크루명입니다.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user  # 요청한 유저 (리더)
        
        # 초대코드 생성 (예: 8자리 랜덤 문자열)
        invitecode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        crew = Crew.objects.create(
            leader=user,
            crewname=validated_data['crewname'],
            type=validated_data['type'],
            invitecode=invitecode,
            member_count=1,
        )
        CrewMember.objects.create(crew=crew, user=user)
        return crew