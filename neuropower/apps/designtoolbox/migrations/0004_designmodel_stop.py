# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-08-15 22:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('designtoolbox', '0003_designmodel_w'),
    ]

    operations = [
        migrations.AddField(
            model_name='designmodel',
            name='stop',
            field=models.IntegerField(default=0),
        ),
    ]