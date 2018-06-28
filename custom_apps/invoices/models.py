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
from django.utils.functional import cached_property
from decimal import Decimal


# An invoice (e.g. https://drive.google.com/file/d/1XWeqbQ-VRXV4C4zy6mOwv2Sasnwpv2WO/view) has multiple work orders
# and a work order has multiple jobs
# that document has rows of jobs joined with their work orders


SERVICE_TIME_CHOICES = (
    ('Midnight - 4 AM','Midnight - 4 AM'),
    ('4 AM - 8 AM', '4 AM - 8 AM'),
    ('8AM - Noon', '8 AM - Noon'),
    ('Noon - 4 PM', 'Noon - 4 PM'),
    ('4 PM - 8 PM', '4 PM - 8 PM'),
    ('8 PM - Midnight', '8 PM - Midnight'),
)

PLOW_COUNT = (
    (0,0),
    (1,1),
)

SALT_COUNT = (
    (0,0),
    (1,1),
    (2, 2),
)

INVOICE_STATUSES = (
    ('not_created','Safety Report - Initial'),
    ('safety_report', 'Closeout Report Generated'),
    ('preliminary_created', 'Preliminary Invoice - In Progress'),
    ('submitted', 'Invoice Submitted - In Review'),
    ('reviewed', 'Reviewed'),
    ('dispute', 'In Dispute'),
    ('finalized', 'Finalized'),
)


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

    #audit = AuditTrailWatcher()

    class Meta:
        verbose_name = 'Service Provider'

    def __str__(self):
        return '{0}'.format(self.name)


class RegionalAdmin(BaseModel):
    name = models.CharField('Regional manager\'s company name', max_length=100)
    system_user = models.ForeignKey('auth.User')

    #audit = AuditTrailWatcher()

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

    #audit = AuditTrailWatcher()


class Invoice(AddressMetadataStorageMixin, BaseModel):
    service_provider = models.ForeignKey('invoices.Vendor')
    remission_address = AddressField('remission address', null=True, blank=True)
    storm_name = models.CharField(max_length=255, null=True, blank=True)
    storm_date = models.DateField(verbose_name="Report Date", null=True, blank=True)
    status = models.CharField(max_length=255, choices=INVOICE_STATUSES, default='not_created', null=True, blank=True)
    dispute_status = models.CharField(max_length=255, null=True, blank=True, default='')
    weather_ready = models.BooleanField(default=False)

    verbose_name = 'Closeout Reports'

    # objects = InvoiceManger()

    def __str__(self):
        return 'Invoice # {0}'.format(self.id)

    #audit = AuditTrailWatcher()

    @property
    def aggregate_snowfall(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.snowfall
        return predicted_values

    @property
    def aggregate_refreeze(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.snowfall
        return predicted_values

    @property
    def aggregate_predicted_salts(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.aggregate_predicted_salts
        return predicted_values

    @property
    def aggregate_predicted_plows(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.aggregate_predicted_plows
        return predicted_values

    @property
    def aggregate_predicted_plow_cost(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.aggregate_predicted_plow_cost
        return predicted_cost

    @property
    def aggregate_predicted_salt_cost(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.aggregate_predicted_salt_cost
        return predicted_cost

    @property
    def aggregate_invoiced_plows(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.aggregate_invoiced_plows
        return predicted_values

    @property
    def aggregate_invoiced_salts(self):
        predicted_values = 0
        for work_order in self.workorder_set.all():
            predicted_values += work_order.aggregate_invoiced_salts
        return predicted_values


    @property
    def aggregate_invoiced_plow_cost(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.aggregate_invoiced_plow_cost
        return predicted_cost

    @property
    def aggregate_invoiced_salt_cost(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.aggregate_predicted_salt_cost
        return predicted_cost

    @property
    def aggregate_predicted_storm_total(self):
        predicted_cost = self.aggregate_predicted_salt_cost + self.aggregate_predicted_plow_cost
        return predicted_cost

    @property
    def aggregate_invoiced_storm_total(self):
        predicted_cost = self.aggregate_invoiced_salt_cost + self.aggregate_invoiced_plow_cost
        return predicted_cost

    @property
    def locations(self):
        return self.workorder_set.count()

    @property
    def storm_days_forecast(self):
        first_sr = self.safetyreport_set.all().first()
        last_sr = self.safetyreport_set.all().last()
        first = ''
        last = ''
        if first_sr:
            first = first_sr.storm_days
        if last_sr:
            last = first_sr.storm_days
        return '{0}'.format(first)

    @property
    def storm_days_invoiced(self):
        first_sr = self.workorder_set.all().first()
        last_sr = self.workorder_set.all().last()
        first = ''
        last = ''
        if first_sr:
            first = first_sr.storm_days
        if last_sr:
            last = first_sr.storm_days
        return '{0}'.format(first)

    @property
    def total_cost_delta(self):
        return self.aggregate_predicted_storm_total - self.aggregate_invoiced_storm_total

    # @property
    @property
    def marked_safe_count(self):
        return self.safetyreport_set.first().safetyvisit_set.filter(safe_to_open=True).count()

    # @property
    @property
    def serviced_count(self):
        return self.safetyreport_set.first().safetyvisit_set.filter(site_serviced=True).count()

    # @property
    @property
    def total_safety_count(self):
        return self.safetyreport_set.first().safetyvisit_set.count()

    @property
    def aggregate_plow_delta(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.plow_delta
        return predicted_cost

    @property
    def aggregate_salt_delta(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.salt_delta
        return predicted_cost

    @property
    def aggregate_plow_cost_delta(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.plow_cost_delta
        return predicted_cost

    @property
    def aggregate_salt_cost_delta(self):
        predicted_cost = 0
        for work_order in self.workorder_set.all():
            predicted_cost += work_order.salt_cost_delta
        return predicted_cost

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
    weather_station = models.ForeignKey('invoices.WeatherStation', null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)

    deice_rate = DollarsField('Cost per de-icing w/o tax', default=0)
    deice_tax = DollarsField('Tax per de-icing', default=0)
    plow_rate = DollarsField('Cost per plow w/o tax', default=0)
    plow_tax = DollarsField('Tax per plow', default=0)
    service_provider = models.ForeignKey('invoices.Vendor', related_name='vendor_locations', null=True, blank=True)
    facility_manager = models.ForeignKey('auth.User', null=True, blank=True)

    objects = BuildingManager()
    #audit = AuditTrailWatcher()

    def __str__(self):
        if self.building_code:
            return 'BC#: {0} - {1} '.format(self.building_code, self.address)
        return 'ID: {0} - {1} '.format(self.id, self.address)


class WorkOrderID(BaseModel):
    work_order_code = models.CharField(max_length=255)
    vendor = models.ForeignKey('invoices.Vendor', null=True, blank=True)
    available = models.BooleanField(default=True)


class WeatherStation(BaseModel):
    station_name = models.CharField(max_length=255, null=True, blank=True)
    short_name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    zip_codes = models.CommaSeparatedIntegerField(max_length=255, null=True, blank=True)
    nws_code = models.CharField(max_length=255, null=True, blank=True)
    cst_reference = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.short_name


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
    last_service_date = models.DateField(help_text='Date of the last service', blank=True, null=True)
    is_discrepant = models.BooleanField(default=False)

    tracker = FieldTracker()
    #audit = AuditTrailWatcher()

    def __str__(self):
        return '{0}'.format(self.work_order_code)

    # def get_plow_count(self):
    #     return self.

    @property
    def has_ice(self):
        try:
            # has_ice = _query_accumulation_data(self.building.zip_code,
            #                                    settings.DEMO_SNOWFALL_DATA_START,
            #                                    settings.DEMO_SNOWFALL_DATA_END)['has_ice']
            # return has_ice if has_ice else 0
            return Decimal(1)
        except Exception as e:
            print(e)
            return 0

    @property
    def snowfall(self):
        try:
            # snowfall = _query_accumulation_data(self.building.zip_code,
            #                                     settings.DEMO_SNOWFALL_DATA_START,
            #                                     settings.DEMO_SNOWFALL_DATA_END)['snowfall']
            # return snowfall if snowfall else 0
            return Decimal(1)
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_plows(self):
        try:
            snowfall = self.snowfall
            predicted = snowfall / 2
            return predicted
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_salts(self):
        try:
            refreeze = self.has_ice
            predicted = 2 if refreeze else 2
            return predicted
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_plow_cost(self):
        try:
            snowfall = self.snowfall
            if snowfall:
                return (self.aggregate_predicted_plows * self.building.plow_rate) + self.building.plow_tax
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_salt_cost(self):
        try:
            refreeze = self.has_ice
            if refreeze:
                return (self.aggregate_predicted_salts * self.building.deice_rate) + self.building.deice_tax
        except Exception as e:
            print(e)
            return 0


    @property
    def aggregate_invoiced_plows(self):
        try:
            invoiced_count = 0
            invoiced_values = self.workvisit_set.values_list('num_plows', flat=True)
            for item in invoiced_values:
                invoiced_count += item
            return invoiced_count
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_invoiced_salts(self):
        try:
            snowfall = self.snowfall
            invoiced_count = 0
            invoiced_values = self.workvisit_set.values_list('num_salts', flat=True)
            for item in invoiced_values:
                invoiced_count += item
            return invoiced_count
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_storm_total(self):
        return self.aggregate_predicted_plow_cost + self.aggregate_predicted_salt_cost

    @property
    def storm_days(self):
        try:
            return '2'
        except:
            return '2'

    @property
    def deice_rate(self):
        return self.building.deice_rate

    @property
    def deice_tax(self):
        return self.building.deice_tax

    @property
    def plow_rate(self):
        return self.building.plow_rate

    @property
    def plow_tax(self):
        return self.building.plow_tax

    @property
    def service_provider(self):
        return self.building.service_provider

    @property
    def aggregate_invoiced_plow_cost(self):
        try:
            return (Decimal(self.aggregate_invoiced_plows) * Decimal(self.building.plow_rate)) + Decimal(self.building.plow_tax)
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_invoiced_salt_cost(self):
        try:
            return (Decimal(self.aggregate_invoiced_salts) * Decimal(self.building.deice_rate)) + Decimal(self.building.deice_tax)
        except Exception as e:
            print(e)
            return 0

    @property
    def plow_delta(self):
        return Decimal(self.aggregate_predicted_plows) - Decimal(self.aggregate_invoiced_plows)

    @property
    def salt_delta(self):
        return Decimal(self.aggregate_predicted_salts) - Decimal(self.aggregate_invoiced_salts)

    @property
    def plow_cost_delta(self):
        return Decimal(self.plow_delta) * self.building.plow_rate

    @property
    def salt_cost_delta(self):
        return Decimal(self.salt_delta) * self.building.deice_rate


# manager for the below relation
class WorkVisitManager(models.Manager):
    def get_queryset(self):
        return super(WorkVisitManager, self).get_queryset().annotate(
            deice_fee=models.Case(
                models.When(num_salts__gte=1, then=
                models.F('work_order__building__deice_rate') + models.F('work_order__building__deice_tax')),
                default=models.Value(0),
                output_field=DollarsField('Cost billed for deicing')),
            plow_fee=models.Case(
                models.When(num_plows__gte=1, then=
                models.F('work_order__building__plow_rate') + models.F('work_order__building__plow_tax')),
                default=models.Value(0),
                output_field=DollarsField('Cost billed for plowing')),
        ).annotate(
            visit_subtotal=models.F('deice_fee') + models.F('plow_fee'),
        )


class WorkVisit(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder', null=True, blank=True)
    service_date = models.DateField(help_text='Date the service was performed', blank=True, null=True)
    service_time = models.CharField(help_text='Last time serviced', max_length=255, null=True, blank=True, choices=SERVICE_TIME_CHOICES)
    num_plows = models.IntegerField('# Plows', null=True, blank=True, default=0, choices=PLOW_COUNT)
    num_salts = models.IntegerField('# Salts', null=True, blank=True, default=0, choices=SALT_COUNT)
    failed_service = models.BooleanField('Service Failed?', default=False)

    #audit = AuditTrailWatcher()
    # aggregates = WorkVisitManager()

    def __str__(self):
        return 'Work for WO#: {0} on {1}'.format(self.work_order.id, self.service_time)


class SafetyReport(BaseModel):
    invoice = models.ForeignKey('invoices.Invoice', null=True, blank=True)
    building = models.ForeignKey('invoices.Building', null=True, blank=True)
    inspection_date = models.DateField(help_text='Date of the safety check', blank=True, null=True, default='2017-12-08')
    site_serviced = models.BooleanField('Site Serviced?', default=True)
    safe_to_open = models.BooleanField('Safe to open site?', default=True)
    safety_concerns = models.CharField('Concerns/Extra Instructions', max_length=255, blank=True, null=True)
    haul_stack_status = models.IntegerField('Snow hauling or stacking required?', choices=SnowStatus.choices(), default=0, null=True, blank=True)
    haul_stack_estimate = DollarsField('Cost estimate for future snow hauling or stacking', default=0, null=True, blank=True)

    #audit = AuditTrailWatcher()

    def __str__(self):
        return 'Safety Report #{0} for'.format(self.id)

    @property
    def has_ice(self):
        try:
            # has_ice = _query_accumulation_data(self.building.zip_code,
            #                                    settings.DEMO_SNOWFALL_DATA_START,
            #                                    settings.DEMO_SNOWFALL_DATA_END)['has_ice']
            # return has_ice if has_ice else 0
            return 1
        except Exception as e:
            print(e)
            return 0

    @property
    def snowfall(self):
        try:
            # snowfall = _query_accumulation_data(self.building.zip_code,
            #                                     settings.DEMO_SNOWFALL_DATA_START,
            #                                     settings.DEMO_SNOWFALL_DATA_END)['snowfall']
            # return snowfall if snowfall else 0
            return 1
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_plows(self):
        try:
            predicted = self.snowfall / 2
            return predicted
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_salts(self):
        try:
            refreeze = self.has_ice
            predicted = 2 if refreeze else 2
            return predicted
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_plow_cost(self):
        try:
            snowfall = self.snowfall
            return (self.aggregate_predicted_plows * self.building.plow_rate) + self.building.plow_tax
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_salt_cost(self):
        try:
            refreeze = self.has_ice
            if refreeze:
                return (self.aggregate_predicted_salts * self.building.deice_rate) + self.building.deice_tax
        except Exception as e:
            print(e)
            return 0

    @property
    def aggregate_predicted_storm_total(self):
        return self.aggregate_predicted_plow_cost + self.aggregate_predicted_salt_cost

    @property
    def storm_days(self):
        try:
            return '12-06-2017'
        except:
            return '12-10-2017'

    @property
    def deice_rate(self):
        return self.building.deice_rate

    @property
    def deice_tax(self):
        return self.building.deice_tax

    @property
    def plow_rate(self):
        return self.building.plow_rate

    @property
    def plow_tax(self):
        return self.building.plow_tax

    @property
    def service_provider(self):
        return self.building.service_provider



class SafetyVisit(BaseModel):
    safety_report = models.ForeignKey('invoices.SafetyReport', null=True, blank=True)
    inspection_date = models.DateField(help_text='Date of the safety check', blank=True, null=True, default='2017-12-08')
    site_serviced = models.BooleanField('Site Serviced?', default=True)
    safe_to_open = models.BooleanField('Safe to open site?', default=True)
    safety_concerns = models.CharField('Concerns/Extra Instructions', max_length=255, blank=True, null=True)
    haul_stack_status = models.IntegerField('Snow hauling or stacking required?', choices=SnowStatus.choices(), default=0, null=True, blank=True)
    haul_stack_estimate = DollarsField('Cost estimate for future snow hauling or stacking', default=0, null=True, blank=True)

    #audit = AuditTrailWatcher()

    def __str__(self):
        return 'Safety Report #{0} for'.format(self.id)


class DiscrepancyReport(BaseModel):
    work_order = models.ForeignKey('invoices.WorkOrder', null=True, blank=True)
    author = models.CharField('author', max_length=100)
    status = models.TextField('Discrepancy communication')

    #audit = AuditTrailWatcher()

    def __str__(self):
        return 'Discrepancy Report #%s for %s' % (self.id, self.work_order)


# Vendor Proxies

class SafetyReportVendor(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Safety Report'

    def __str__(self):
        return 'Safety Report # {0}'.format(self.id)

class InvoiceVendor(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Invoice'

    def __str__(self):
        return 'Invoice # {0}'.format(self.id)


# NWA Proxies

class ServiceForecastNWA(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Service Forecast'

    def __str__(self):
        return 'Service Forecast for Inv # {0}'.format(self.id)

class DiscrepancyReportNWA(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Discrepancy Report'

    def __str__(self):
        return 'Discrepancy Report for Inv # {0}'.format(self.id)

class ServiceForecastItemNWA(SafetyReport):
    class Meta(SafetyReport.Meta):
        proxy = True
        verbose_name = 'Safety Report'

    def __str__(self):
        return 'SR for Inv. # {0}'.format(self.invoice.id)

class DiscrepancyReportItemNWA(WorkOrder):
    class Meta(WorkOrder.Meta):
        proxy = True
        verbose_name = 'Work Order'

    def __str__(self):
        return 'Work Order {0} for Inv # {1}'.format(self.id, self.invoice.id)

class SubmittedInvoiceNWA(Invoice):
    class Meta(Invoice.Meta):
        proxy = True
        verbose_name = 'Invoice'

    def __str__(self):
        return 'Invoice # {0}'.format(self.id)