# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-14 12:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0011_auto_20180514_0830'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='work_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]