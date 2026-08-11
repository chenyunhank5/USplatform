from django.db import migrations, models


DEFAULT_TERMS_HTML = (
    "<h2>User Registration Agreement</h2>"
    "<p>Welcome to Landor.</p>"
    "<p>Please read these Terms and Conditions carefully before using this "
    "website. By registering or continuing to use the platform, you confirm "
    "that you understand and accept these terms.</p>"
    "<h3>1. User information</h3>"
    "<p>You agree to provide accurate registration information and to keep "
    "your account credentials secure.</p>"
    "<h3>2. Platform use</h3>"
    "<p>You agree to use the platform lawfully and in accordance with the "
    "rules shown on this page.</p>"
)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0031_rebrand_landor"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name="terms_and_conditions_html",
            field=models.TextField(default=DEFAULT_TERMS_HTML),
        ),
    ]
