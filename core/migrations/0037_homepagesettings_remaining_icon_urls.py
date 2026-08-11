from django.db import migrations, models


FIELDS = {
    "default_profile_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628056/profile_h2zimj.png",
    "order_description_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778637234/order_description_wf0ij5.png",
    "please_note_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778637234/note_vmbnnb.png",
    "wallet_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778880278/Wallet_evtebh.png",
    "settings_deposit_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628584/card-sendOrange1.f6dd01ed_y9vcf7.png",
    "settings_withdraw_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/withdraw_rrfcwq.png",
    "trading_account_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/trading_account_lbpikk.png",
    "personal_information_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/personal_info_gjvexq.png",
    "official_announcement_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1775312901/download_12_eh4bai.png",
    "more_services_icon_url": "https://res.cloudinary.com/dkwg2x7qd/image/upload/v1778628585/more_service_pm0yuj.png",
}


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0036_homepagesettings_icon_urls"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepagesettings",
            name=name,
            field=models.URLField(default=url, max_length=1000),
        )
        for name, url in FIELDS.items()
    ]
