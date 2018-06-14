# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db.models.query_utils import Q
from django.forms import HiddenInput
from nested_admin.nested import NestedModelAdmin, NestedStackedInline

from custom_apps.data_ingestion.bq import query_for_accumulation_zip
from custom_apps.invoices.enums import WORKFLOW_SPEC
from custom_apps.invoices.models import Building
from custom_apps.utils import maps
from custom_apps.utils.admin_utils import generate_field_getter
from custom_apps.utils.fields import AddressMetadataStorageMixin
from custom_apps.utils.forecast import forecast
from .enums import ReportState
from .models import Invoice, WorkOrder, WorkVisit, SafetyReport, Vendor, VendorSettings, VendorSafetyReport, VendorWorkOrder, Vendor
from django.contrib.admin import AdminSite
from .models import *
from thirdparty.adminactions import actions as actions



from .admin_views.superuser_views import ServiceForecast, DiscrepancyReview, WorkProxyServiceForecast, WorkProxyServiceDiscrepancy

admin.site.register(Vendor)
admin.site.register(WorkProxyServiceForecast, ServiceForecast)
admin.site.register(WorkProxyServiceDiscrepancy, DiscrepancyReview)


class NWASite(AdminSite):
    site_url = None
    site_header = settings.SITE_NAME
    site_title = settings.SITE_NAME
    index_title = settings.SITE_NAME


class CBRESite(AdminSite):
    site_url = None
    site_header = settings.SITE_NAME
    site_title = settings.SITE_NAME
    index_title = settings.SITE_NAME


class VendorSite(AdminSite):
    site_url = None
    site_header = settings.SITE_NAME
    site_title = settings.SITE_NAME
    index_title = settings.SITE_NAME


nwa_site = NWASite(name='nwa_admin')
cbre_site = CBRESite(name='cbre_site')
vendor_site = VendorSite(name='vendor_site')

# from custom_apps.invoices.admin_views import superuser_views
# from custom_apps.invoices.admin_views import cbre_views
# from custom_apps.invoices.admin_views import vendor_views
from custom_apps.invoices.admin_views import nwa_views, vendor_views, cbre_views


nwa_site.register(NWABuilding, nwa_views.NWABuildingAdmin)
nwa_site.register(NWAServiceForecast, nwa_views.ServiceForecast)
nwa_site.register(NWAServiceDiscrepancy, nwa_views.DiscrepancyReview)
nwa_site.register(NWASubmittedInvoiceProxy, nwa_views.NWASubmittedInvoiceAdmin)

cbre_site.register(CBRESafetyProxy, cbre_views.InvoiceAdmin)
cbre_site.register(CBREInvoiceProxy, cbre_views.PrelimInvoiceAdmin)

# vendor_site.register(VendorSafetyProxy, vendor_views.InvoiceAdmin)
# vendor_site.register(VendorInvoiceProxy, vendor_views.PrelimInvoiceAdmin)
# vendor_site.register(DiscrepancyReport, vendor_views.DiscrepancyReportAdmin)

vendor_site.register(VendorSafetyReport, vendor_views.VendorSafetyReportManager)
vendor_site.register(VendorWorkOrder, vendor_views.VendorWorkOrderManager)

actions.add_to_site(admin.site)
actions.add_to_site(nwa_site)
actions.add_to_site(cbre_site)
actions.add_to_site(vendor_site)
