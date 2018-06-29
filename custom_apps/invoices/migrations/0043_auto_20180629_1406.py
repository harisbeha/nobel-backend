# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-06-29 18:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0042_auto_20180628_2016'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeatherData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('storm_id', models.CharField(blank=True, max_length=100, null=True)),
                ('location_id', models.CharField(blank=True, max_length=100, null=True)),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('precipitation_type', models.CharField(blank=True, max_length=100, null=True)),
                ('precipititation_description', models.CharField(blank=True, max_length=100, null=True)),
                ('total', models.CharField(blank=True, max_length=100, null=True)),
                ('zip_code', models.CharField(blank=True, max_length=100, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('narrative', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='discrepancyreviewvendor',
            options={'verbose_name': 'Work Order Review'},
        ),
    ]
