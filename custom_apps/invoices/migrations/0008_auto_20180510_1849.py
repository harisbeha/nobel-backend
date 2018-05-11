# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-10 22:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0007_auto_20180510_0047'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoiceproxydiscrepancy',
            options={'verbose_name': 'Discrepancy Report'},
        ),
        migrations.AlterModelOptions(
            name='invoiceproxyprelim',
            options={'verbose_name': 'Preliminary Invoice'},
        ),
        migrations.AlterModelOptions(
            name='invoiceproxyvendor',
            options={'verbose_name': 'Generate Safety Report'},
        ),
        migrations.AddField(
            model_name='building',
            name='building_code',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='building',
            name='short_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='safetyreport',
            name='haul_stack_estimate',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=8, null=True, verbose_name='Cost estimate for future snow hauling or stacking'),
        ),
        migrations.AlterField(
            model_name='safetyreport',
            name='haul_stack_status',
            field=models.IntegerField(blank=True, choices=[(0, 'NONE'), (1, 'NEEDS_STACKING'), (2, 'NEEDS_HAULING')], default=0, null=True, verbose_name='Snow hauling or stacking required?'),
        ),
    ]