from django.db import models
from crew.models import Crew
from crew.models import CrewMember

# Create your models here.
class Notice(models.Model):
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class NoticeReaction(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE)

    REACTION_CHOICES = [
        ('present', '참가'), 
        ('absent', '불참')
    ]
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
