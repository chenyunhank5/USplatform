from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0037_homepagesettings_remaining_icon_urls"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="my_team_icon_url",
            field=models.URLField(
                default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/personal_info_gjvexq.png",
                max_length=1000,
            ),
        ),
    ]
