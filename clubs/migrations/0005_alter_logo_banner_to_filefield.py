# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clubs", "0004_club_banner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="logo",
            field=models.FileField(blank=True, null=True, upload_to="club_logos/"),
        ),
        migrations.AlterField(
            model_name="club",
            name="banner",
            field=models.FileField(
                blank=True,
                help_text="Optional banner image for the club",
                null=True,
                upload_to="club_banners/",
            ),
        ),
    ]
