
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('crew', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='crew',
            name='leader',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='led_crews', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='crewmember',
            name='crew',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='crew.crew'),
        ),
        migrations.AddField(
            model_name='crewmember',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='crew_memberships', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='crewmember',
            unique_together={('crew', 'user')},
        ),
    ]
