# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from nested_admin.nested import NestedModelAdmin, NestedStackedInline

from custom_apps.utils.admin_utils import generate_field_getter
from .models import Invoice, WorkOrder, Job, Vendor


class CustomModelAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != "id"]
        super(CustomModelAdmin, self).__init__(model, admin_site)


class BaseInline(NestedStackedInline):
    extra = 0


class JobInline(BaseInline):
    model = Job


class WorkOrderInline(BaseInline):
    model = WorkOrder
    inlines = [JobInline]


class InvoiceAdmin(NestedModelAdmin):
    get_vendor_name = generate_field_getter('vendor.name', 'Vendor Name')
    get_vendor_address = generate_field_getter('vendor.address', 'Vendor Address')
    list_display = [get_vendor_name, get_vendor_address, 'invoice_number', 'remission_address']

    search_fields = ['vendor__name', 'invoice_number']
    list_filter = ['vendor__name']
    inlines = [WorkOrderInline]


class VendorAdmin(admin.ModelAdmin):
    pass


admin.site.register(Vendor, VendorAdmin)
admin.site.register(Invoice, InvoiceAdmin)
