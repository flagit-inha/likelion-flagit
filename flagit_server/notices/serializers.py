from rest_framework import serializers
from notices.models import Notice, NoticeReaction

class NoticeReactionSerializer(serializers.ModelSerializer):
    crew_member_nickname = serializers.CharField(source='crew_member.user.nickname', read_only=True)
    
    class Meta:
        model = NoticeReaction
        fields = ['crew_member', 'reaction', 'crew_member_nickname']
        read_only_fields = ['crew_member']

class NoticeSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    reactions = serializers.SerializerMethodField()
    reaction_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Notice
        fields = ['title', 'content', 'created_at', 'reactions', 'reaction_summary']
        read_only_fields = ['created_at']
    
    def get_reactions(self, obj):
        reactions = NoticeReaction.objects.filter(notice=obj)
        return NoticeReactionSerializer(reactions, many=True).data
    
    def get_reaction_summary(self, obj):
        reactions = NoticeReaction.objects.filter(notice=obj)
        present = reactions.filter(reaction='present').count()
        absent = reactions.filter(reaction='absent').count()
        
        return {
            'present': present,
            'absent': absent
        }