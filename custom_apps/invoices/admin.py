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
from .models import Invoice, WorkOrder, WorkVisit, SafetyReport, Vendor, VendorSettings


from .admin_views.superuser_views import ServiceForecast, DiscrepancyReview, WorkProxyServiceForecast, WorkProxyServiceDiscrepancy

admin.site.register(WorkProxyServiceForecast, ServiceForecast)
admin.site.register(WorkProxyServiceDiscrepancy, DiscrepancyReview)
