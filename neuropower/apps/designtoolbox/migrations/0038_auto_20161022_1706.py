# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-10-22 17:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('designtoolbox', '0037_auto_20161022_0053'),
    ]

    operations = [
        migrations.RenameField(
            model_name='designmodel',
            old_name='ITI',
            new_name='ITIfixed',
        ),
        migrations.RenameField(
            model_name='designmodel',
            old_name='ITImax',
            new_name='ITItruncmax',
        ),
        migrations.RenameField(
            model_name='designmodel',
            old_name='ITImean',
            new_name='ITItruncmean',
        ),
        migrations.RenameField(
            model_name='designmodel',
            old_name='ITImin',
            new_name='ITItruncmin',
        ),
        migrations.AddField(
            model_name='designmodel',
            name='ITImodel',
            field=models.IntegerField(choices=[(1, 'fixed'), (2, 'truncated exponential'), (3, 'uniform')], default=3),
        ),
        migrations.AddField(
            model_name='designmodel',
            name='ITIunifmax',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='designmodel',
            name='ITIunifmin',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
