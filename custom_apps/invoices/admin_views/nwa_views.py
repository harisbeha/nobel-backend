from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin

from ..models import *
from ..resources import *
from django.forms.models import BaseModelFormSet

from django.forms.models import BaseInlineFormSet, BaseFormSet
import nested_admin
from import_export.admin import ExportMixin
from django.conf.urls import url
from django.shortcuts import HttpResponseRedirect
import sendgrid
import os
from sendgrid.helpers.mail import *
from .helpers import get_locations_by_system_user
from .admin_forms import WOFormSet, SRFormSet
from admin_comments.admin import CommentInline


# Subinlines

class WorkVisitProxyInline(nested_admin.NestedTabularInline):
    model = WorkVisit
    extra = 1
    readonly_fields = []
    classes = ['collapse']

class SubmittedWorkOrderInline(nested_admin.NestedTabularInline):
    model = WorkVisit
    extra = 1
    readonly_fields = ['num_plows', 'num_salts', 'service_failed']
    classes = ['collapse']

# Inlines

class WorkOrderInline(nested_admin.NestedTabularInline):
    model = WorkOrder
    formset = WOFormSet
    inlines = [WorkVisitProxyInline]
    readonly_fields = ['deice_rate', 'deice_tax', 'plow_rate', 'plow_tax']


    def get_fields(self, request, obj=None):
        fields = super(WorkOrderInline, self).get_fields(request, obj)
        rate_fields = fields[10:14]
        new_fields = fields[0:4] + rate_fields + fields[5:9]
        return new_fields

    def deice_rate(self, obj):
        return obj.building.deice_rate

    def deice_tax(self, obj):
        return obj.building.deice_tax

    def plow_rate(self, obj):
        return obj.building.plow_rate

    def plow_tax(self, obj):
        return obj.building.plow_tax

    def get_formset(self, *args, **kwargs):
        formset = super(WorkOrderInline, self).get_formset(*args, **kwargs)
        return formset

    def get_formset(self, request, obj=None, **kwargs):
        """
        Pre-populating formset using GET params
        """
        initial = []
        if request.method == "GET":
            pass
        formset = super(WorkOrderInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            return 0
        return get_locations_by_system_user(request.user).count()


class SafetyReportInline(admin.TabularInline):
    model = SafetyReport
    formset = SRFormSet

    def get_formset(self, *args, **kwargs):
        formset = super(SafetyReportInline, self).get_formset(*args, **kwargs)
        return formset

    def get_formset(self, request, obj=None, **kwargs):
        """
        Pre-populating formset using GET params
        """
        initial = []
        if request.method == "GET":
            #
            # Populate initial based on request
            #
            locations = get_locations_by_system_user(request.user).values('id')
            # print(locations.count())
            for l in locations:
                initial.append({'building': str(l['id']), 'site_serviced': True, 'safe_to_open': True, 'service_time': '2017-12-09'})
            # initial.append({
            #     'building': locations,
            # })
        formset = super(SafetyReportInline, self).get_formset(request, obj, **kwargs)
        formset.__init__ = curry(formset.__init__, initial=initial)
        formset.request = request
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            # Don't add any extra forms if the related object already exists.
            return 0
        return get_locations_by_system_user(request.user).count()




# Model Admins



class ServiceForecastAdmin(admin.ModelAdmin):
    model = ServiceForecastNWA
    list_filter = ('id', 'storm_name', 'storm_date', 'service_provider')
    list_display = ['safety_report_url', 'id', 'service_provider', 'locations',
                    'aggregate_snowfall', 'aggregate_refreeze', 'storm_days_forecast',
                    'aggregate_predicted_salts', 'aggregate_predicted_plows', 'aggregate_predicted_salt_cost',
                    'aggregate_predicted_plow_cost', 'aggregate_predicted_storm_total']

    def safety_report_url(self, obj):
        return '<a href="/nwa/invoices/serviceforecastitemnwa/?invoice__id={0}">{1}</a>'.format(obj.id, obj.id)

    safety_report_url.allow_tags = True
    safety_report_url.short_description = 'Safety Report'


class ServiceForecastItemAdmin(admin.ModelAdmin):
    model = ServiceForecastItemNWA
    list_filter = ('invoice_id',)
    list_display = ['id', 'invoice_id', 'service_provider', 'building', 'deice_rate',
                    'deice_tax', 'plow_rate',
                    'plow_tax', 'snowfall', 'storm_days', 'has_ice',
                    'aggregate_predicted_salts', 'aggregate_predicted_plows', 'aggregate_predicted_salt_cost',
                    'aggregate_predicted_plow_cost', 'aggregate_predicted_storm_total']


class DiscrepancyReport(admin.ModelAdmin, ExportMixin):
    model = DiscrepancyReportNWA
    resource_class=InvoiceResource
    list_filter = ('id',)
    generated_discrept_dict = {}
    list_display = ['show_id_url', 'discrepancy_count', 'id', 'service_provider', 'locations', 'aggregate_snowfall', 'aggregate_refreeze',
                    'storm_days_invoiced', 'aggregate_refreeze', 'aggregate_invoiced_salts', 'aggregate_predicted_salts', 'aggregate_salt_delta',
                    'aggregate_invoiced_plows', 'aggregate_predicted_plows', 'aggregate_plow_delta', 'aggregate_salt_cost_delta',
                    'aggregate_plow_cost_delta', 'total_cost_delta']

    def show_id_url(self, obj):
        return '<a href="/nwa/invoices/discrepancyreportitemnwa/?invoice__id={0}">{1}</a>'.format(obj.id, obj.id)

    show_id_url.allow_tags = True
    show_id_url.short_description = 'Invoice'

    def aggregate_salt_delta(self, obj):
        try:
            if obj.aggregate_salt_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.aggregate_salt_delta)
            else:
                return obj.aggregate_salt_delta
        except Exception as e:
            print(e)
            return 0

    aggregate_salt_delta.allow_tags = True

    def aggregate_plow_delta(self, obj):
        try:
            if obj.aggregate_plow_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.aggregate_plow_delta)
            else:
                return obj.aggregate_plow_delta
        except Exception as e:
            print(e)
            return 0

    aggregate_plow_delta.allow_tags = True

    def aggregate_salt_cost_delta(self, obj):
        try:
            if obj.aggregate_salt_cost_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.aggregate_salt_cost_delta)
            else:
                return obj.aggregate_salt_cost_delta
        except Exception as e:
            print(e)
            return 0

    aggregate_salt_cost_delta.allow_tags = True

    def aggregate_plow_cost_delta(self, obj):
        try:
            if obj.aggregate_plow_cost_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.aggregate_plow_cost_delta)
            else:
                return obj.aggregate_plow_cost_delta
        except Exception as e:
            print(e)
            return 0

    aggregate_plow_cost_delta.allow_tags = True


class DiscrepancyReportItemAdmin(admin.ModelAdmin, ExportMixin):
    model = DiscrepancyReportItemNWA
    resource_class=InvoiceResource
    list_filter = ('invoice__id',)
    inlines = [CommentInline,]
    actions = ['override_discrepancy']
    list_display = ['view_work_order', 'is_discrepant', 'invoice', 'service_provider', 'building', 'deice_rate',
                    'deice_tax', 'plow_rate',
                    'plow_tax', 'snowfall', 'storm_days', 'has_ice',
                    'aggregate_predicted_salts', 'aggregate_invoiced_salts', 'salt_delta', 'aggregate_predicted_plows',
                    'aggregate_invoiced_plows', 'plow_delta', 'salt_cost_delta', 'plow_cost_delta']

    generated_discrept_dict = {}


    def override_discrepancy(self, request, queryset):
        rows_updated = queryset.update(is_discrepant=False)
        return HttpResponseRedirect("/nwa/invoices/discrepancyreportnwa/")

    def view_work_order(self, obj):
        # return u'<a href="/nwa/invoices/discrepancyreportitemnwa/?invoice__id={0}">{1}</a>'.format(obj.id, obj.work_order_code)
        return '{0}'.format(obj.work_order_code)

    def salt_delta(self, obj):
        try:
            if obj.salt_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.salt_delta)
            else:
                return obj.salt_delta
        except Exception as e:
            print(e)
            return 0

    salt_delta.allow_tags = True

    def plow_delta(self, obj):
        try:
            if obj.plow_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.plow_delta)
            else:
                return obj.plow_delta
        except Exception as e:
            print(e)
            return 0

    plow_delta.allow_tags = True

    def salt_cost_delta(self, obj):
        try:
            if obj.salt_cost_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.salt_cost_delta)
            else:
                return obj.salt_cost_delta
        except Exception as e:
            print(e)
            return 0

    salt_cost_delta.allow_tags = True

    def plow_cost_delta(self, obj):
        try:
            if obj.plow_cost_delta > 0:
                return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(obj.plow_cost_delta)
            else:
                return obj.plow_cost_delta
        except Exception as e:
            print(e)
            return 0

    plow_cost_delta.allow_tags = True

class SubmittedInvoiceAdmin(nested_admin.NestedModelAdmin):
    exclude=['remission_address', 'address_info_storage']
    list_display=['invoices', 'status']
    inlines = [SubmittedWorkOrderInline]
    readonly_fields = []
    limited_manytomany_fields = {}

    actions = ['approve_invoice']

    def get_queryset(self, request):
        qs = super(SubmittedInvoiceAdmin, self).get_queryset(request)
        return qs.filter(status__in=['submitted'])

    def get_readonly_fields(self, request, obj=None):
            return ['status', 'storm_name', 'storm_date', 'dispute_status', 'status', 'dispute_status', 'service_provider']

    def invoices(self, obj):
        return obj

    def approve_invoice(self, request, queryset):
        rows_updated = queryset.update(status='approved')
        return HttpResponseRedirect("/nwa/invoices/discrepancyreportnwa/")