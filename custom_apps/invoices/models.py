# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import pre_save

from custom_apps.utils import maps
from ..utils.models import BaseModel


# An invoice (e.g. https://drive.google.com/file/d/1XWeqbQ-VRXV4C4zy6mOwv2Sasnwpv2WO/view) has multiple work orders
# and a work order has multiple jobs
# that document has rows of jobs joined with their work orders


def AddressField(fullname):
    return models.TextField(fullname, max_length=500)


class Vendor(BaseModel):
    name = models.CharField('company name of the vendor', max_length=100)
    address = AddressField('full mailing address')

    def __str__(self):
        return self.name


class Invoice(BaseModel):
    vendor = models.ForeignKey('invoices.Vendor')
    invoice_number = models.CharField('numerical identifier for the invoice', max_length=50)

    # The above two fields are the "primary key"
    class Meta(BaseModel.Meta):
        unique_together = (('vendor', 'invoice_number'),)
        abstract = False  # we inherit an abstract class and mark it final in this incarnation

    remission_address = AddressField('full mailing addresses to send remission')


# manager for the below relation
class WorkOrderManager(models.Manager):
    def get_queryset(self):
        return super(WorkOrderManager, self).get_queryset().annotate(
            deice_cost=models.F("deice_rate") + models.F("deice_tax"),
            plow_cost=models.F("plow_rate") + models.F("plow_tax"),
        )


class WorkOrder(BaseModel):
    order_number = models.CharField('textual work order number, e.g. TDU12345678', max_length=50)
    invoice = models.ForeignKey('invoices.Invoice')

    # The above two fields are the "primary key"
    class Meta(BaseModel.Meta):
        unique_together = (('invoice', 'order_number'),)
        abstract = False  # we inherit an abstract class and mark it final in this incarnation

    storm_name = models.CharField('name of the storm work to which work is being done in response', max_length=100)
    building_id = models.CharField('identifier for the building on which work was done', max_length=50)
    building_address = AddressField('full address of the building on which work was done')

    deice_rate = models.DecimalField(
        'cost in dollars without tax per de-icing service', max_digits=8, decimal_places=2)
    deice_tax = models.DecimalField(
        'tax in dollars per de-icing service', max_digits=8, decimal_places=2)
    plow_rate = models.DecimalField(
        'cost in dollars without tax per plow service',
        max_digits=8, decimal_places=2)
    plow_tax = models.DecimalField(
        'tax in dollars per plow service', max_digits=8, decimal_places=2)

    objects = WorkOrderManager()  # makes extra _cost fields summing tax + rate appear on each query


# manager for the below relation
class JobManager(models.Manager):
    def get_queryset(self):
        return super(JobManager, self).get_queryset().annotate(
            deice_fee=models.Case(
                models.When(provided_deicing=True, then=
                models.F('work_order__deice_rate') + models.F('work_order__deice_tax')),
                default=models.Value(0),
                output_field=models.DecimalField(max_digits=8, decimal_places=2)),
            plow_fee=models.Case(
                models.When(provided_plowing=True, then=
                models.F('work_order__plow_rate') + models.F('work_order__plow_tax')),
                default=models.Value(0),
                output_field=models.DecimalField(max_digits=8, decimal_places=2)),
        ).annotate(
            visit_subtotal=models.F('deice_fee') + models.F('plow_fee'),
        )


class Job(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder')
    response_time_start = models.DateTimeField('time clocked in')
    response_time_end = models.DateTimeField('time clocked out')

    provided_deicing = models.BooleanField('were de-icing services provided?')
    provided_plowing = models.BooleanField('were plowing services provided (includes plowing and shoveling ONLY)?')

    objects = JobManager()


validatable_models = {id(WorkOrder): 'building_address',
                      id(Vendor): 'address',
                      id(Invoice): 'remission_address'}
def validation_handler(sender, instance, **kwargs):
    model = type(instance)
    field_name = validatable_models[id(model)]
    address = getattr(instance, field_name)
    formal_address = maps.formalize_address(address)

    if not formal_address:
        raise ValidationError('Address not found on Google')
    setattr(instance, field_name, formal_address)

pre_save.connect(validation_handler, WorkOrder)
pre_save.connect(validation_handler, Vendor)
pre_save.connect(validation_handler, Invoice)
