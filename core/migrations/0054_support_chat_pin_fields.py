from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0053_guest_cleanup_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='support_is_pinned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='support_pin_order',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
