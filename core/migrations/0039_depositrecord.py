from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_homepagesettings_my_team_icon_url"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DepositRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("transaction_id", models.CharField(default=core.models.generate_deposit_id, max_length=50, unique=True)),
                ("status", models.CharField(default="completed", max_length=20)),
                ("remark", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_deposit_records", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deposit_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
    ]
