from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0052_userprofile_reset_counters'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_hidden_from_staff',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='last_activity_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
