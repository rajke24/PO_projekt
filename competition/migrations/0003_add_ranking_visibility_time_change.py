# Generated by Django 3.1.2 on 2021-01-27 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0002_auto_20210123_2247'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='ranking_visibility_change_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
