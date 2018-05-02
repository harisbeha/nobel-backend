# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from audit_trail import AuditTrailWatcher
from django.db import models
from model_utils import FieldTracker

from custom_apps.invoices.enums import *
from custom_apps.utils.fields import AddressField, DollarsField, AddressMetadataStorageMixin
from ..utils.models import BaseModel
from custom_apps.data_ingestion.bq import query_for_accumulation_zip
from django.conf import settings

# An invoice (e.g. https://drive.google.com/file/d/1XWeqbQ-VRXV4C4zy6mOwv2Sasnwpv2WO/view) has multiple work orders
# and a work order has multiple jobs
# that document has rows of jobs joined with their work orders


class VendorSettings(BaseModel):
    class Meta:
        verbose_name_plural = 'Vendor settings'

    const_a = models.IntegerField()
    const_b = models.IntegerField()
    vendor = models.OneToOneField('invoices.Vendor', related_name='settings')


class Vendor(AddressMetadataStorageMixin, BaseModel):
    name = models.CharField('Vendor\'s company name', max_length=100)
    address = AddressField('Full mailing address')
    system_user = models.ForeignKey('auth.User')
    region = models.ForeignKey('invoices.RegionalAdmin')

    audit = AuditTrailWatcher()

    def __str__(self):
        return self.name


class RegionalAdmin(BaseModel):
    name = models.CharField('Regional manager\'s company name', max_length=100)
    system_user = models.ForeignKey('auth.User')

    audit = AuditTrailWatcher()

    def __str__(self):
        return self.name


# class InvoiceManger(models.Manager):
#     def get_queryset(self):
#         return super(InvoiceManger, self).get_queryset().annotate(
#             state=models.Min('workorder__job__state', output_field=models.IntegerField(choices=ReportState.choices()))
#         )


class Invoice(AddressMetadataStorageMixin, BaseModel):
    vendor = models.ForeignKey('invoices.Vendor')
    remission_address = AddressField('Full mailing addresses to send remission', null=True, blank=True)

    # objects = InvoiceManger()

    def __str__(self):
        return 'Invoice %s for %s' % (self.id, self.vendor.name)

    audit = AuditTrailWatcher()


# manager for the below relation
class BuildingManager(models.Manager):
    def get_queryset(self):
        return super(BuildingManager, self).get_queryset().annotate(
            deice_cost=models.F("deice_rate") + models.F("deice_tax"),
            plow_cost=models.F("plow_rate") + models.F("plow_tax"),
        )


class Building(AddressMetadataStorageMixin, BaseModel):
    address = AddressField('Full building address')
    type = models.IntegerField('Type of property', choices=BuildingType.choices())

    deice_rate = DollarsField('Cost without tax per de-icing service')
    deice_tax = DollarsField('Tax per de-icing service')
    plow_rate = DollarsField('Cost without tax per plow service')
    plow_tax = DollarsField('Tax per plow service')

    objects = BuildingManager()
    audit = AuditTrailWatcher()

    def __str__(self):
        return 'Building#%s at %s' % (self.id, self.address)


# manager for the below relation
class WorkOrderManager(models.Manager):
    def get_queryset(self):
        return super(WorkOrderManager, self).get_queryset().annotate(
            work_start=models.Min('workvisit__response_time_start'),
            work_end=models.Max('workvisit__response_time_end'),
        )


class WorkOrder(BaseModel):
    vendor = models.ForeignKey('invoices.Vendor', blank=True)
    invoice = models.ForeignKey('invoices.Invoice', blank=True, null=True)
    building = models.ForeignKey('invoices.Building')

    storm_name = models.CharField('Name of the event for which work is being done in response', max_length=100)
    storm_date = models.DateField('Date of the last storm event')
    last_service_date = models.DateField('Date of last service at this location')

    flag_safe = models.BooleanField('Property safe to open?', null=False, default=False)
    flag_visitsdocumented = models.BooleanField('all information about work visits entered?', null=False,
                                                default=False)
    flag_weatherready = models.BooleanField('Spending forecast generated for work order?',
                                            null=False, default=False)
    flag_failure = models.NullBooleanField('Service failure marked by cbre?', null=True, default=None)
    flag_hasdiscrepancies = models.NullBooleanField(
        'Discrepancies in forecasted/actual spending for the work order?', null=True, default=None)
    flag_hasdiscrepanciesfailure = models.BooleanField(
        'Vendor failed to provide a satisfactory response to the discrepancies?', null=False, default=False)
    flag_completed = models.BooleanField('Sent to the vendor on a finalized invoice?',
                                         null=False, default=False)

    objects = WorkOrderManager()  # makes extra _cost fields summing tax + rate appear on each query
    tracker = FieldTracker()
    audit = AuditTrailWatcher()

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.vendor.name)

    @property
    def has_ice(self):
        try:
            has_ice = query_for_accumulation_zip(self.building.address_info_storage['postal_code'],
                                             settings.DEMO_SNOWFALL_DATA_START,
                                             settings.DEMO_SNOWFALL_DATA_END)['has_ice']
            return has_ice
        except Exception as e:
            return ''

    @property
    def snowfall(self):
        try:
            snowfall = query_for_accumulation_zip(self.building.address_info_storage['postal_code'],
                                             settings.DEMO_SNOWFALL_DATA_START,
                                             settings.DEMO_SNOWFALL_DATA_END)['snowfall']
            return snowfall
        except Exception as e:
            return ''

    @property
    def duration(self):
        try:
            duration = query_for_accumulation_zip(self.building.address_info_storage['postal_code'],
                                             settings.DEMO_SNOWFALL_DATA_START,
                                             settings.DEMO_SNOWFALL_DATA_END)['duration']
            return duration
        except Exception as e:
            return ''

# manager for the below relation
class WorkVisitManager(models.Manager):
    def get_queryset(self):
        return super(WorkVisitManager, self).get_queryset().annotate(
            deice_fee=models.Case(
                models.When(provided_deicing=True, then=
                models.F('work_order__building__deice_rate') + models.F('work_order__building__deice_tax')),
                default=models.Value(0),
                output_field=DollarsField('Cost billed for deicing')),
            plow_fee=models.Case(
                models.When(provided_plowing=True, then=
                models.F('work_order__building__plow_rate') + models.F('work_order__building__plow_tax')),
                default=models.Value(0),
                output_field=DollarsField('Cost billed for plowing')),
        ).annotate(
            visit_subtotal=models.F('deice_fee') + models.F('plow_fee'),
        )


class WorkVisit(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder')
    response_time_start = models.DateTimeField('Time clocked in')
    response_time_end = models.DateTimeField('Time clocked out')

    provided_deicing = models.BooleanField('De-icing services provided?')
    provided_plowing = models.BooleanField('Plowing services provided? (includes plowing and shoveling ONLY)')

    audit = AuditTrailWatcher()
    objects = WorkVisitManager()

    def __str__(self):
        return 'Work for %s on %s' % (
            self.work_order.id, self.response_time_start.strftime('%b %e, %l:%M %p'))


class SafetyReport(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder')
    safe_to_open = models.BooleanField('Safe to open site?')
    safety_concerns = models.TextField('Any concerns? Let us know of all site conditions', max_length=1000, blank=True)
    snow_instructions = models.TextField('Extra instructions for handling remaining snow', max_length=1000, blank=True)
    haul_stack_status = models.IntegerField('Snow hauling or stacking required?', choices=SnowStatus.choices())
    haul_stack_estimate = DollarsField('Cost estimate for future snow hauling or stacking', default=0)

    audit = AuditTrailWatcher()

    def __str__(self):
        return 'Safety Report #%s for %s' % (self.id, self.work_order)


class DiscrepancyReport(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder')
    author = models.CharField('author', max_length=100)
    message = models.TextField('Discrepancy communication')

    audit = AuditTrailWatcher()

    def __str__(self):
        return 'Discrepancy Report #%s for %s' % (self.id, self.work_order)


# Proxies

class RegionalAdminProxyNWA(RegionalAdmin):
    class Meta(RegionalAdmin.Meta):
        proxy = True
        verbose_name = 'Create CBRE admin'

    def __str__(self):
        return 'CBRE admin %s' % (self.name)


class WorkOrderProxyNWA(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Check for discrepancies in work order'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.vendor.name)


class VendorProxyCBRE(Vendor):
    class Meta(Vendor.Meta):
        proxy = True
        verbose_name = 'Create new vendor'

    def __str__(self):
        return 'Vendor %s' % (self.name)


class WorkOrderProxyCBRE(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Check work orders for failure'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.vendor.name)


class WorkOrderProxyVendor(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Create and manage work order'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.vendor.name)
