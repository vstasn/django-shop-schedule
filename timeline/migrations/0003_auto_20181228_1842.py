# Generated by Django 2.1.4 on 2018-12-28 18:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_auto_20181228_0853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='daysoff',
            name='from_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
