import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_viplevel_maximum_withdrawal_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawalrequest',
            name='transaction_id',
            field=models.CharField(
                max_length=50,
                unique=True,
                blank=True,
                null=True
            ),
        ),
    ]
