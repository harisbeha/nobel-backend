# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-06-29 00:16
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0041_auto_20180628_0509'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscrepancyReviewVendor',
            fields=[
            ],
            options={
                'verbose_name': 'Work Order (Review)',
                'abstract': False,
                'proxy': True,
                'indexes': [],
            },
            bases=('invoices.workorder',),
        ),
        migrations.AlterField(
            model_name='safetyreport',
            name='verify_weather',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
        migrations.AlterField(
            model_name='workorder',
            name='verify_weather',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, null=True),
        ),
    ]
