# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from django.contrib import admin

from custom_apps.utils.admin_utils import generate_field_getter
from .models import Invoice


class CustomModelAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != "id"]
        super(CustomModelAdmin, self).__init__(model, admin_site)





class InvoiceAdmin(admin.ModelAdmin):
    get_vendor_name = generate_field_getter('vendor.name', 'Vendor Name')
    get_vendor_address = generate_field_getter('vendor.address', 'Vendor Address')
    list_display = [get_vendor_name, get_vendor_address, 'invoice_number', 'remission_address', 'first_event']
    #list_display = ['storm_name',
    #                'building',
    #                'vendor__name',
    #                'deice_rate',
    #                'deice_tax'
    #                'deice_cost',
    #                'plow_rate',
    #                'plow_tax',
    #                'plow_cost',
    #                'order_number',


admin.site.register(Invoice, InvoiceAdmin)
