from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0032_homepagesettings_terms_and_conditions_html"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="transaction_notice_html",
            field=models.TextField(default="<h2>Transaction Notice</h2><p>Important transaction announcements will be published here.</p>"),
        ),
        migrations.AddField(
            model_name="homepagesettings",
            name="campaign_html",
            field=models.TextField(default="<h2>Campaign</h2><p>Current campaign information will be published here.</p>"),
        ),
        migrations.AddField(
            model_name="homepagesettings",
            name="illustrate_html",
            field=models.TextField(default="<h2>Illustrate</h2><p>Platform instructions and illustrations will be published here.</p>"),
        ),
        migrations.AddField(
            model_name="homepagesettings",
            name="faqs_html",
            field=models.TextField(default="<h2>Frequently Asked Questions</h2><h3>How do I use the platform?</h3><p>Please follow the instructions shown on each page.</p>"),
        ),
        migrations.AddField(
            model_name="homepagesettings",
            name="company_profile_html",
            field=models.TextField(default="<h2>Company Profile</h2><p>Company information will be published here.</p>"),
        ),
    ]
