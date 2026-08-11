from django.db import migrations, models


FIELDS = {
    "withdrawal_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312902/download_4_ijox13.png",
    "deposit_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312902/download_5_flfcf2.png",
    "customer_service_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_6_x6blhw.png",
    "transaction_notice_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_7_exqqzc.png",
    "campaign_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_8_uczm9q.png",
    "illustrate_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_9_yfakmr.png",
    "faqs_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_10_laivzw.png",
    "company_profile_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_11_nepxza.png",
    "home_nav_active_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_o2t6x5.png",
    "home_nav_inactive_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/ohome.0cf9ec80_edaksd.png",
    "records_nav_active_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_1_gzqqjd.png",
    "records_nav_inactive_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/orecords.44d9036b_pjxc8m.png",
    "order_nav_active_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/startingActive3.f51cf26f_dnesyh.png",
    "order_nav_inactive_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775245492/ostarting.8b1ceecf_ko8hha.png",
    "messages_nav_active_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243935/download_2_fjlpca.png",
    "messages_nav_inactive_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/omessages.7280e6e4_ht6fcx.png",
    "settings_nav_active_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243934/download_3_gu3ks5.png",
    "settings_nav_inactive_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775243799/oprofile.e21aa036_bkgray.png",
}


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0035_homepagesettings_order_information"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name=name,
            field=models.URLField(default=url, max_length=1000),
        )
        for name, url in FIELDS.items()
    ]
