from django.db import models
from crew.models import Crew
from crew.models import CrewMember

# Create your models here.
class Notice(models.Model):
    crew = models.ForeignKey(Crew, on_delete=models.CASCADE)
    content = models.TextField()


class NoticeReaction(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE)

    REACTION_CHOICES = [('GOOD', 'GOOD'), ('BAD', 'BAD')]
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
