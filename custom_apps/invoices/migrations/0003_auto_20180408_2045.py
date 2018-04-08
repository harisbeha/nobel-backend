# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-08 20:45
from __future__ import unicode_literals

import custom_apps.invoices.enums
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_auto_20180408_2018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='state',
            field=models.IntegerField(choices=[(-1, b'REJECTED'), (1, b'CREATED'), (2, b'INITIALIZED'), (3, b'SAFETY_REVIEWED'), (4, b'SAFETY_REVIEW_CLOSED'), (5, b'PRELIM_GENERATED'), (6, b'PRE_FORECAST_REVIEWED'), (7, b'FORECASTED'), (8, b'SENT_TO_PROVIDER'), (9, b'VALIDATED'), (10, b'FINALIZED')], default=custom_apps.invoices.enums.ReportState(1)),
        ),
    ]
