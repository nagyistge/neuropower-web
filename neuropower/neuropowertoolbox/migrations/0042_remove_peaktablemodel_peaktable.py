# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-10 00:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('neuropowertoolbox', '0041_parametermodel_masklocation'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='peaktablemodel',
            name='peaktable',
        ),
    ]
