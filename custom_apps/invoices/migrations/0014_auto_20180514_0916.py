# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-14 13:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0013_auto_20180514_0834'),
    ]

    operations = [
        migrations.RenameField(
            model_name='building',
            old_name='vendor',
            new_name='service_provider',
        ),
        migrations.RenameField(
            model_name='workorder',
            old_name='work_order_id',
            new_name='work_order_code',
        ),
    ]
