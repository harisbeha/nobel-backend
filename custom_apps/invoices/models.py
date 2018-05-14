# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from audit_trail import AuditTrailWatcher
from django.db import models
from model_utils import FieldTracker

from custom_apps.invoices.enums import *
from custom_apps.utils.fields import AddressField, DollarsField, AddressMetadataStorageMixin
from ..utils.models import BaseModel
from custom_apps.data_ingestion.bq import query_for_accumulation_zip, _query_accumulation_data
from django.conf import settings
from django.contrib import admin

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

    class Meta:
        verbose_name = 'Service Provider'

    def __str__(self):
        return '{0}'.format(self.name)


class RegionalAdmin(BaseModel):
    name = models.CharField('Regional manager\'s company name', max_length=100)
    system_user = models.ForeignKey('auth.User')

    audit = AuditTrailWatcher()

    def __str__(self):
        return 'temp'


# class InvoiceManger(models.Manager):
#     def get_queryset(self):
#         return super(InvoiceManger, self).get_queryset().annotate(
#             state=models.Min('workorder__job__state', output_field=models.IntegerField(choices=ReportState.choices()))
#         )

class PrelimInvoice(AddressMetadataStorageMixin, BaseModel):
    vendor = models.ForeignKey('invoices.Vendor', null=True, blank=True)
    storm_name = models.CharField(max_length=255, null=True, blank=True)
    event_start = models.DateField(null=True, blank=True)
    event_end = models.DateField(null=True, blank=True)

    def __str__(self):
        return 'Invoice #: {0}'.format(self.id)

    audit = AuditTrailWatcher()


class Invoice(AddressMetadataStorageMixin, BaseModel):
    service_provider = models.ForeignKey('invoices.Vendor')
    remission_address = AddressField('remission address', null=True, blank=True)
    storm_name = models.CharField(max_length=255, null=True, blank=True)
    storm_date = models.DateField(null=True, blank=True)

    verbose_name = 'Closeout Reports'

    # objects = InvoiceManger()

    def __str__(self):
        return 'Invoice # {0}'.format(self.id)

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
    short_name = models.CharField(max_length=255, null=True, blank=True)
    building_code = models.CharField(max_length=255, null=True, blank=True)

    deice_rate = DollarsField('Cost per de-icing w/o tax', default=0)
    deice_tax = DollarsField('Tax per de-icing', default=0)
    plow_rate = DollarsField('Cost per plow w/o tax', default=0)
    plow_tax = DollarsField('Tax per plow', default=0)
    service_provider = models.ForeignKey('invoices.Vendor', related_name='vendor_locations', null=True, blank=True)

    objects = BuildingManager()
    audit = AuditTrailWatcher()

    def __str__(self):
        if self.building_code:
            return 'BC#: {0} - {1} '.format(self.building_code, self.address)
        return 'ID: {0} - {1} '.format(self.id, self.address)


# manager for the below relation
class WorkOrderManager(models.Manager):
    def get_queryset(self):
        return super(WorkOrderManager, self).get_queryset().annotate(
            work_start=models.Min('workvisit__response_time_start'),
            work_end=models.Max('workvisit__response_time_end'),
        )


class WorkOrder(BaseModel):
    work_order_code = models.CharField(max_length=255, blank=True, null=True)
    service_provider = models.ForeignKey('invoices.Vendor', null=True, blank=True)
    invoice = models.ForeignKey('invoices.Invoice', blank=True, null=True)
    building = models.ForeignKey('invoices.Building', null=True, blank=True)

    storm_name = models.CharField(help_text='Name of the event for which work is being done in response', max_length=100, blank=True, null=True)
    storm_date = models.DateField(help_text='Date of the last storm event', blank=True, null=True)
    last_service_date = models.DateField(help_text='Date of last service at this location', null=True, blank=True)

    # flag_safe = models.BooleanField(help_text='Property safe to open?', null=False, default=False)
    # flag_visitsdocumented = models.BooleanField(help_text='all information about work visits entered?', null=False,
    #                                             default=False)
    # flag_weatherready = models.BooleanField(help_text='Spending forecast generated for work order?',
    #                                         null=False, default=False)
    # flag_failure = models.NullBooleanField(help_text='Service failure marked by client?', null=True, default=None)
    # flag_hasdiscrepancies = models.NullBooleanField(
    #     help_text='Discrepancies in forecasted/actual spending for the work order?', null=True, default=None)
    # flag_hasdiscrepanciesfailure = models.BooleanField(
    #     help_text='Vendor failed to provide a satisfactory response to the discrepancies?', null=False, default=False)
    # flag_completed = models.BooleanField(help_text='Sent to the vendor on a finalized invoice?',
    #                                      null=False, default=False)
    num_plows = models.IntegerField('# Plows', null=True, blank=True, default=0)
    num_salts = models.IntegerField('# Salts', null=True, blank=True, default=0)
    failed_service = models.BooleanField('Service Failed?', default=False)

    tracker = FieldTracker()
    audit = AuditTrailWatcher()

    def __str__(self):
        return '{0}'.format(self.work_order_code)

    @property
    def has_ice(self):
        try:
            has_ice = _query_accumulation_data(self.building.address_info_storage['postal_code'],
                                               settings.DEMO_SNOWFALL_DATA_START,
                                               settings.DEMO_SNOWFALL_DATA_END)['has_ice']
            return has_ice
        except Exception as e:
            return ''

    @property
    def snowfall(self):
        try:
            snowfall = _query_accumulation_data(self.building.address_info_storage['postal_code'],
                                                settings.DEMO_SNOWFALL_DATA_START,
                                                settings.DEMO_SNOWFALL_DATA_END)['snowfall']
            return snowfall
        except Exception as e:
            return ''

    @property
    def duration(self):
        try:
            duration = _query_accumulation_data(self.building.address_info_storage['postal_code'],
                                                settings.DEMO_SNOWFALL_DATA_START,
                                                settings.DEMO_SNOWFALL_DATA_END)['duration']
            return duration
        except Exception as e:
            return ''

    @property
    def predicted_amount(self):
        try:
            snowfall = int(self.snowfall)
            if snowfall < 3:
                return snowfall * self.building.deice_rate + self.building.deice_tax
            else:
                return ((3 * self.building.deice_rate) + self.building.deice_tax) + \
                       (((snowfall - 3) * self.building.plow_rate) + self.building.plow_tax)
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
    work_order = models.ForeignKey('invoices.WorkOrder', null=True, blank=True)
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
    invoice = models.ForeignKey('invoices.Invoice', null=True, blank=True)
    building = models.ForeignKey('invoices.Building', null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)
    safe_to_open = models.BooleanField('Safe to open site?')
    safety_concerns = models.CharField('Any concerns? Let us know of all site conditions', max_length=255, blank=True)
    snow_instructions = models.CharField('Extra instructions for handling remaining snow', max_length=255, blank=True)
    haul_stack_status = models.IntegerField('Snow hauling or stacking required?', choices=SnowStatus.choices(), default=0, null=True, blank=True)
    haul_stack_estimate = DollarsField('Cost estimate for future snow hauling or stacking', default=0, null=True, blank=True)

    audit = AuditTrailWatcher()

    def __str__(self):
        return 'Safety Report #{0} for'.format(self.id)


class DiscrepancyReport(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder', null=True, blank=True)
    author = models.CharField('author', max_length=100)
    message = models.TextField('Discrepancy communication')

    audit = AuditTrailWatcher()

    def __str__(self):
        return 'Discrepancy Report #%s for %s' % (self.id, self.work_order)


# Proxies

class RegionalAdminProxyNWA(RegionalAdmin):
    class Meta(RegionalAdmin.Meta):
        proxy = True
        verbose_name = 'internal regional admin'

    def __str__(self):
        return 'CBRE admin %s' % ('temp')


class WorkOrderProxyNWA(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'discrepancy reviewable work order'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.service_provider.name)

class InvoiceForecastReportProxyNWA(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'forecast report work order'

    def __str__(self):
        return 'Invoice #%s' % (self.id)

class VendorProxyCBRE(Vendor):
    class Meta(Vendor.Meta):
        proxy = True
        verbose_name = 'client vendor'

    def __str__(self):
        return 'Vendor %s' % ('temp')


class WorkOrderProxyCBRE(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'reviewable work orders'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.service_provider.name)


class WorkOrderProxyVendor(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'vendor work order'

    def __str__(self):
        return 'WO#%s for %s' % (self.id, self.service_provider.name)


class InvoiceProxyVendor(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Generate Safety Report'

    def __str__(self):
        return 'Invoice Draft (Safety Report Batch) %s' % (self.id)

class InvoiceProxyForecast(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Forecast Report'

    def __str__(self):
        return 'Inv # %s' % 'temp'

class InvoiceProxyDiscrepancy(RegionalAdmin):
    class Meta(RegionalAdmin.Meta):
        proxy = True
        verbose_name = 'Discrepancy Report'

    def __str__(self):
        return 'Inv # %s' % 'temp'


class InvoiceProxyPrelim(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Create Preliminary Invoice'

    def __str__(self):
        return 'Invoice # {0}'.format(self.id)


class WorkProxyServiceForecast(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Service Forecast'

    def __str__(self):
        return '{0} - {1}'.format(self.invoice_id, self.id)


class WorkProxyServiceDiscrepancy(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Discrepancy Report'

    def __str__(self):
        return '{0} - {1}'.format(self.invoice_id, self.id)


class ModifiablePrelimInvoice(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Modify Preliminary Invoice'

    def __str__(self):
        return '{0} - {1}'.format(self.invoice_id, self.id)