# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-18 23:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('neuropowertoolbox', '0020_auto_20160218_2243'),
    ]

    operations = [
        migrations.AddField(
            model_name='mixturemodel',
            name='a',
            field=models.DecimalField(decimal_places=4, default='NaN', max_digits=10),
        ),
    ]