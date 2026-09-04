from django.db import migrations


def rebrand_lazarev(apps, schema_editor):
    HomePageSettings = apps.get_model("core", "HomePageSettings")

    for settings in HomePageSettings.objects.all():
        if settings.brand_name and settings.brand_name.strip().lower() == "landor":
            settings.brand_name = "LAZAREV"
        if settings.terms_and_conditions_html:
            settings.terms_and_conditions_html = settings.terms_and_conditions_html.replace(
                "Landor", "Lazarev"
            )
        settings.save(update_fields=["brand_name", "terms_and_conditions_html"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0043_userprofile_authorized_amount"),
    ]

    operations = [
        migrations.RunPython(rebrand_lazarev, migrations.RunPython.noop),
    ]
