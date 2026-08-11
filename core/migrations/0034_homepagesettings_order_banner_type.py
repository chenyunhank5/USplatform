from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0033_homepagesettings_managed_content_pages"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="order_banner_type",
            field=models.CharField(
                choices=[("image", "Image"), ("video", "Video")],
                default="image",
                max_length=10,
            ),
        ),
    ]
