# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-06-02 00:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0032_building_facility_manager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='safetyvisit',
            name='snow_instructions',
        ),
        migrations.AlterField(
            model_name='invoice',
            name='storm_date',
            field=models.DateField(blank=True, null=True, verbose_name='Report Date'),
        ),
        migrations.AlterField(
            model_name='safetyvisit',
            name='safety_concerns',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Concerns/Extra Instructions'),
        ),
    ]
