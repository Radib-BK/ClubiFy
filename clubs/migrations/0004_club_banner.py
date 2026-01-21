# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0003_club_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='banner',
            field=models.ImageField(blank=True, help_text='Optional banner image for the club', null=True, upload_to='club_banners/'),
        ),
    ]
