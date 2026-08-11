from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_homepagesettings_order_banner_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="order_description_html",
            field=models.TextField(
                default="<h2>Order Description</h2><p>Order instructions and information will be published here.</p>"
            ),
        ),
        migrations.AddField(
            model_name="homepagesettings",
            name="please_note_html",
            field=models.TextField(
                default="<h2>Please Note</h2><p>Important order notices will be published here.</p>"
            ),
        ),
    ]
