from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0039_depositrecord"),
    ]

    operations = [
        migrations.AddField(
            model_name="depositrecord",
            name="is_read_by_user",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="withdrawalrequest",
            name="is_read_by_user",
            field=models.BooleanField(default=False),
        ),
    ]
