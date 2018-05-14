# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-14 12:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0009_auto_20180513_2149'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModifiablePrelimInvoice',
            fields=[
            ],
            options={
                'verbose_name': 'Modify Preliminary Invoice',
                'abstract': False,
                'proxy': True,
                'indexes': [],
            },
            bases=('invoices.workorder',),
        ),
        migrations.AlterModelOptions(
            name='invoiceproxyprelim',
            options={'verbose_name': 'Create Preliminary Invoice'},
        ),
        migrations.AlterModelOptions(
            name='vendor',
            options={'verbose_name': 'Service Provider'},
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_completed',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_failure',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_hasdiscrepancies',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_hasdiscrepanciesfailure',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_safe',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_visitsdocumented',
        ),
        migrations.RemoveField(
            model_name='workorder',
            name='flag_weatherready',
        ),
    ]
