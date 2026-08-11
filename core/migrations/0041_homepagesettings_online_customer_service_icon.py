from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_transaction_read_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="online_customer_service_icon_url",
            field=models.URLField(
                default="https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_2_fjlpca.png",
                max_length=1000,
            ),
        ),
    ]
