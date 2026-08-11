from django.db import migrations, models


def set_landor_brand(apps, schema_editor):
    HomePageSettings = apps.get_model("core", "HomePageSettings")
    HomePageSettings.objects.filter(
        brand_name__iexact="MAJOR TOM"
    ).update(brand_name="LANDOR")


def restore_major_tom_brand(apps, schema_editor):
    HomePageSettings = apps.get_model("core", "HomePageSettings")
    HomePageSettings.objects.filter(
        brand_name__iexact="LANDOR"
    ).update(brand_name="MAJOR TOM")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_homepagesettings_order_banner_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homepagesettings",
            name="brand_name",
            field=models.CharField(default="LANDOR", max_length=100),
        ),
        migrations.RunPython(
            set_landor_brand,
            restore_major_tom_brand,
        ),
    ]
