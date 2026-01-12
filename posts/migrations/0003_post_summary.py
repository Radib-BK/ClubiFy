# Generated manually for adding summary field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='summary',
            field=models.TextField(blank=True, help_text='AI-generated summary of the post', null=True),
        ),
    ]
