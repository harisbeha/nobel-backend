from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin
from django.shortcuts import HttpResponseRedirect
from django.conf.urls import url
from django.forms import ModelForm
import sendgrid
import os
from sendgrid.helpers.mail import *
from django.conf import settings
from import_export.admin import ExportMixin

from ..models import *
from ..resources import *
from django.forms.models import BaseModelFormSet

from django.forms.models import BaseInlineFormSet, BaseFormSet
import nested_admin
from raven import Client

client = Client('https://4d87c7cd417f4e14be43597f3ffac1b3:d46f2a1776a54a8a80d3d8ab57717c71@sentry.io/1219530')



# all the views in this file should be visible only to the superuser
class SuperuserModelAdmin(ImportExportActionModelAdmin):
    exclude = ['address_info_storage']
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return False


def total_plows(self, obj=None):
    return 1

def total_salts(self, obj=None):
    return 2

def invoice(self, obj=None):
    return self.invoice

def vendor(self, obj=None):
    return self.service_provider

def service_provider(self, obj=None):
    return self.service_provider

def location(self, obj=None):
    return self.building

def deicing_rate(self, obj=None):
    return self.building.deice_rate

def deicing_tax(self, obj=None):
    return self.building.deice_tax

def plow_rate(self, obj=None):
    return self.building.plow_rate

def plow_tax(self, obj=None):
    return self.building.plow_tax

def work_order(self, obj=None):
    return self.work_order_code

def deicing_fee(self, obj=None):
    try:
        cost = self.building.deice_rate * self.num_salts
        return str(cost)
    except:
        return ''

def plow_fee(self, obj=None):
    try:
        cost = self.building.plow_rate * self.num_plows
        return str(cost)
    except:
        return ''

def storm_total(self, obj=None):
    total = str((self.building.plow_rate * self.num_plows) + (self.building.deice_rate * self.num_salts))
    return total

def snowfall(self, obj=None):
    return 1.4

def storm_days(self, obj=None):
    return 2

def refreeze(self, obj=None):
    return '0'

def number_salts(self, obj=None):
    return self.num_salts

def number_salts_predicted(self, obj=None):
    try:
        pred = self.num_salts - 1
        if pred >= 0:
            return pred
        else:
            return 0
    except:
        return ''
    # #print(self.__dict__)
    # import random
    # return random.randint(1,3)

def number_plows_predicted(self, obj=None):
    try:
        pred = self.num_plows - 1
        if pred >= 0:
            return pred
        else:
            return 0
    except:
        return ''

def salts_delta(self, obj=None):
    return '3'

def number_plows(self, obj=None):
    return self.num_plows

def push_delta(self, obj=None):
    return '4'

def deicing_cost_delta(self, obj=None):
    return '$128.99'

def plowing_cost_delta(self, obj=None):
    return '$199.10'

def get_locations_by_system_user(user=None, provider=None):
    # vendor = Vendor.objects.filter(system_user__email='VENDOR@VENDOR.com')[0]
    #print(provider)
    if provider:
        locations = Building.objects.filter(service_provider=provider)
    else:
        vend = Vendor.objects.get(system_user=user)
        locations = Building.objects.filter(service_provider=vend)
    return locations


class SafetyReportForm(ModelForm):
    fields = '__all__'
    model = SafetyReport

    def __init__(self, *args, **kwargs):
        super(SafetyReportForm, self).__init__(*args, **kwargs)
        # init_build = self.initial.get('building')
        # b = Building.objects.get(id=init_build).service_provider
        # self.fields.building.queryset = Building.objects.filter(service_provider=b)



class SRFormSet(BaseInlineFormSet):
    model = SafetyReport
    # form = SafetyReportForm

    def __init__(self, *args, **kwargs):
        super(SRFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            init_build = form.initial.get('building')
            b = Building.objects.get(id=init_build).service_provider
            form.fields['building'].queryset = Building.objects.filter(service_provider=b)
        if self.request.user.is_superuser:
            #print('yes')
            self.locations = get_locations_by_system_user(None, self.instance.service_provider)
        else:
            self.locations = get_locations_by_system_user(self.request.user, None)


from django.forms import ModelForm
# class WOrderForm(ModelForm):
#     fields = ['vendor', 'building', 'number_plows', 'number_salts']


class WOFormSet(BaseInlineFormSet):
    model = WorkOrder

    def __init__(self, *args, **kwargs):
        super(WOFormSet, self).__init__(*args, **kwargs)
        if self.request.user.is_superuser:
            #print('yes')
            self.locations = get_locations_by_system_user(None, self.instance.service_provider)
        else:
            self.locations = get_locations_by_system_user(self.request.user, None)


from django.utils.functional import curry




class WorkVisitProxyInline(nested_admin.NestedTabularInline):
    model = WorkVisit
    extra = 1
    readonly_fields = []
    classes = ['collapse']


class WorkOrderInline(nested_admin.NestedTabularInline):
    model = WorkOrder
    formset = WOFormSet
    inlines = [WorkVisitProxyInline]
    readonly_fields = ['deice_rate', 'deice_tax', 'plow_rate', 'plow_tax', 'subtotal']


    def get_fields(self, request, obj=None):
        fields = super(WorkOrderInline, self).get_fields(request, obj)
        rate_fields = fields[11:16]
        new_fields = fields[0:4] + rate_fields + fields[5:11]
        return new_fields

    def deice_rate(self, obj):
        return obj.building.deice_rate

    def deice_tax(self, obj):
        return obj.building.deice_tax

    def plow_rate(self, obj):
        return obj.building.plow_rate

    def plow_tax(self, obj):
        return obj.building.plow_tax

    def subtotal(self, obj):
        return '${0}'.format(float(obj.aggregate_invoiced_plow_cost) + float(obj.aggregate_invoiced_salt_cost))

    def get_formset(self, *args, **kwargs):
        formset = super(WorkOrderInline, self).get_formset(*args, **kwargs)
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
            if request.user.is_superuser:
                locations = Building.objects.filter(service_provider=obj.service_provider).values_list('id', flat=True)
            else:
                vend = Vendor.objects.get(system_user=request.user)
                locations = Building.objects.filter(service_provider=vend).values_list('id', flat=True)
            s_name = None if not obj else obj.storm_name
            s_date = '2017-12-10' if not obj else obj.storm_date
            s_provider = None if not obj else obj.service_provider

            for l in locations:
                #print({'building': str(l['id']), 'service_provider': s_provider,
                                # 'storm_name': s_name,'report_date': s_date,
                                # 'last_service_date': '2017-12-09', 'num_plows':0, 'num_salts':0,
                                # 'failed_service':False, 'work_order_code':'Td1290'})
                initial.append({})
        formset = super(WorkOrderInline, self).get_formset(request, obj, **kwargs)
        formset.__init__ = curry(formset.__init__, initial=initial)
        formset.request = request
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            return 0
        return len(get_locations_by_system_user(request.user).values_list('id', flat=True))

class SafetyVisitProxyInline(nested_admin.NestedTabularInline):
    model = SafetyVisit
    extra = 1
    classes = []

class SafetyReportInline(nested_admin.NestedTabularInline):
    model = SafetyReport
    form = SafetyReportForm
    formset = SRFormSet
    inlines = [SafetyVisitProxyInline]

    def get_formset(self, request, obj=None, **kwargs):
        """
        Pre-populating formset using GET params
        """
        initial = []
        if request.method == "GET":
            #
            # Populate initial based on request
            #
            if request.user.is_superuser and obj.service_provider:
                locations = Building.objects.filter(service_provider=obj.service_provider).values_list('id', flat=True)
                vend = obj.service_provider
            else:
                vend = Vendor.objects.get(system_user=request.user)
                locations = Building.objects.filter(service_provider=vend).values_list('id', flat=True)

            for l in locations:
                initial.append({'building': str(l), 'safe_to_open': True, 'service_provider_id': str(vend.id)})
        formset = super(SafetyReportInline, self).get_formset(request, obj, **kwargs)
        formset.__init__ = curry(formset.__init__, initial=initial)
        formset.request = request
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            return 0
        return len(get_locations_by_system_user(request.user).values_list('id', flat=True))

    def save_formset(self, request, form, formset, change):
        try:
            instances = formset.save(commit=False)
            safe = []
            for inst in instances:
                if inst.safe_to_open:
                    safe.append(inst)
            not_safe = instances.exclude(safe).values_list('name', flat=True)
            not_safe_count = not_safe.count()
            send_to = instances[0].building.facility_manager.email
            if not_safe == 0:
                message_bit = "All buildings safe to open"
            else:
                message_bit = "%s buildings not safe to open" % not_safe_count
            self.message_user(request, "%s successfully generated." % message_bit)

            sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
            from_email = Email(settings.DEFAULT_FROM_EMAIL)
            to_email = Email(send_to)
            subject = "Closeout Report Generated"
            content = Content("text/plain", "Closeout report generated: {0}".format(
                'http://nobel-weather-dev.herokuapp.com/admin/invoices/workproxyserviceforecast/', 'temp'))
            mail = Mail(from_email, subject, to_email, content)

            for instance in instances:
                instance.save()
            formset.save_m2m()
            invoice = instances.last().invoice
            invoice.status = 'safety_report'
            invoice.save()

        except Exception as e:
            print(e)


# class SafetyInvoiceForm(ModelForm):
#     fields = '__all__'
#     model = SafetyReport
#
#     def __init__(self, *args, **kwargs):
#         super(SafetyInvoiceForm, self).__init__(*args, **kwargs)
#         self.fields['service_provider'].queryset = Vendor.objects.get(id__in=service_provider_id)
#
#         # self.fields.building.queryset = Building.objects.filter(service_provider=b)


@register(InvoiceProxyVendor)
class InvoiceAdmin(nested_admin.NestedModelAdmin):
    exclude=['remission_address', 'address_info_storage']
    list_display=['reports', 'status']
    inlines = [SafetyReportInline]
    readonly_fields = []
    limited_manytomany_fields = {}
    actions=['finalize_safety_report']
    # form = SafetyInvoiceForm

    change_list_template = "admin/provider/safety_report_changelist.html"

    def get_queryset(self, request):
        qs = super(InvoiceAdmin, self).get_queryset(request)
        prelim = VendorSafetyProxy.objects.filter(status__in=['not_created', 'safety_report'],
                                          service_provider__system_user=request.user)
        return prelim

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['service_provider'].queryset = Vendor.objects.filter(system_user=request.user)
        return super(InvoiceAdmin, self).render_change_form(request, context, args, kwargs)

    def get_changeform_initial_data(self, request):
        vend_id = '{0}'.format(Vendor.objects.get(system_user=request.user).id)
        return {'service_provider': vend_id}

    def reports(self, obj):
        return obj

    def get_urls(self):
        urls = super(InvoiceAdmin, self).get_urls()
        my_urls = [
            url('finalize_safety_report/', self.finalize_safety_report),
        ]
        return my_urls + urls

    def finalize_safety_report(self, request, queryset):
        rows_updated = queryset.update(status='preliminary_created')
        return HttpResponseRedirect("/provider/invoices/vendorinvoiceproxy/")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            kwargs["queryset"] = Building.objects.filter(service_provider__system_user=request.user)
        return super(InvoiceAdmin. self).formfield_for_foreignkey(db_field, request, **kwargs)

    finalize_safety_report.short_description = "Generate Closeout Report"



class PrelimInvoiceAdmin(nested_admin.NestedModelAdmin, ImportExportActionModelAdmin):
    resource_class = VendorInvoiceProxyResource
    exclude=['remission_address', 'address_info_storage']
    list_display=['invoices', 'status']
    inlines = [WorkOrderInline]
    limited_manytomany_fields = {}

    def get_queryset(self, request):
        qs = super(PrelimInvoiceAdmin, self).get_queryset(request)
        prelim = VendorInvoiceProxy.objects.filter(status__in=['preliminary_created', 'submitted'],
                                          service_provider__system_user=request.user)
        return prelim

    actions=['finalize_submit_invoice']

    change_list_template = "admin/provider/safety_report_changelist.html"

    def invoices(self, obj):
        return obj

    def get_urls(self):
        urls = super(PrelimInvoiceAdmin, self).get_urls()
        my_urls = [
            url('finalize_submit_invoice/', self.finalize_submit_invoice),
        ]
        return my_urls + urls

    def finalize_submit_invoice(self, request, queryset):
        rows_updated = queryset.update(status='submitted')
        if rows_updated == 1:
            message_bit = "1 invoice was"
        else:
            message_bit = "%s invoices were" % rows_updated
        self.message_user(request, "%s submitted successfully." % message_bit)

        sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        from_email = Email(settings.DEFAULT_FROM_EMAIL)
        to_email = Email("harisbeha@gmail.com")
        subject = "Invoice Submitted"
        invoice_id = queryset[0].id
        content = Content("text/plain", "Invoice #{0} submitted: {1}{2}".format(invoice_id, 'http://nobel-weather-dev.herokuapp.com/admin/invoices/workproxyserviceforecast/', invoice_id))
        mail = Mail(from_email, subject, to_email, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        # #print(response)
        return HttpResponseRedirect("/provider/invoices/vendorinvoiceproxy/")

    finalize_submit_invoice.short_description = "Finalize and submit invoice"


# @register(Invoice)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = Invoice
#     list_display = ['storm_name','report_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [SafetyReportInline]


# @register(InvoiceProxyVendor)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = InvoiceProxyVendor
#     list_display = ['storm_name','report_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [SafetyReportInline]
#     # change_form_template = 'admin/invoice_admin.html'


# @register(InvoiceProxyPrelim)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = InvoiceProxyPrelim
#     list_display = ['storm_name','report_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [WorkOrderInline]
#     change_form_template = 'admin/invoice_admin.html'


# @register(InvoiceProxyForecast)
# class InvoiceForecastAdmin(admin.ModelAdmin):
#
#     pass

class ServiceForecast(admin.ModelAdmin):
    model = WorkProxyServiceForecast
    list_filter = ('invoice_id', 'invoice__storm_name', 'invoice__report_date')
    list_display = [work_order, invoice, service_provider, location, deicing_rate, deicing_tax, plow_rate,
                    plow_tax, snowfall, storm_days, refreeze,
                    number_salts, number_plows, deicing_fee, plow_fee, storm_total]


class DiscrepancyReview(admin.ModelAdmin):
    model = WorkProxyServiceDiscrepancy
    list_filter = ('invoice_id', 'invoice__storm_name', 'invoice__report_date')
    list_display = [work_order, invoice, service_provider, location, deicing_rate, deicing_tax, plow_rate,
                    plow_tax, snowfall, storm_days, refreeze,
                    number_salts, number_salts_predicted, 'salt_delta', number_plows, number_plows_predicted,
                    'push_delta', 'deice_cost_delta', 'plow_cost_delta']


    def salt_delta(self, obj):
        try:
            # pred = self.num_plows - 1
            pred = 1
            return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(pred)
        except Exception as e:
            return ''

    salt_delta.allow_tags = True

    def push_delta(self, obj):
        try:
            # pred = self.num_plows - 1
            pred = 1
            return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format(pred)
        except Exception as e:
            return ''

    push_delta.allow_tags = True

    def deice_cost_delta(self, obj):
        return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format('$129.10')

    deice_cost_delta.allow_tags = True

    def plow_cost_delta(self, obj):
        return u'<div style = "background-color: red; color:white; font-weight:bold; text-align:center;" >{0}</div>'.format('$199.10')

    plow_cost_delta.allow_tags = True


class BuildingAdmin(SuperuserModelAdmin):
    list_display = ['address', 'type']

#
#
@register(RegionalAdmin)
class RegionalManagerAdmin(SuperuserModelAdmin):
    list_display = ['name', 'system_user']
#
#
# @register(VendorSettings)
# class VendorSettingsAdmin(SuperuserModelAdmin):
#     list_display = ['const_a', 'const_b', 'vendor']
#
#
@register(Vendor)
class VendorAdmin(SuperuserModelAdmin):
    list_display = ['name', 'address', 'system_user']
#
#
# @register(WorkOrder)
# class WorkOrderAdmin(SuperuserModelAdmin):
#     list_display = ['vendor', 'invoice', 'building', 'storm_name']
#     raw_id_fields = ("building",)
#
#
# @register(WorkVisit)
# class WorkVisitAdmin(SuperuserModelAdmin):
#     list_display = ['work_order', 'response_time_start', 'response_time_end']
#
#


def report_date(obj):
    return obj.invoice.storm_date


def storm_name(obj):
    return obj.invoice.storm_name

# @register(SafetyReport)
# class SafetyReportAdmin(admin.ModelAdmin):
#     # list_filter = (report_date, report_date)
#     list_display = ['building', storm_name, report_date, 'existing_work_order', 'site_serviced', 'safe_to_open', 'service_time']
#
#     def existing_work_order(self, obj):
#         existing_work_order = WorkOrder.objects.filter(invoice=obj.invoice, building=obj.building).exists()
#         return existing_work_order
#     existing_work_order.boolean = True


# @register(ModifiablePrelimInvoice)
# class ModifyPrelimInvoiceAdmin(admin.ModelAdmin):
#     # list_filter = (report_date, report_date)
#     list_filter = ['invoice_id', 'invoice__storm_name', 'invoice__report_date', 'failed_service']
#     list_editable = ['building', 'last_service_date', 'num_plows', 'num_salts', 'failed_service']
#     list_display = ['id', 'building', service_provider, storm_name, report_date, 'last_service_date',
#                     'num_plows', 'num_salts', 'failed_service']


#
#
class DiscrepancyReportAdmin(SuperuserModelAdmin):
    list_display = ['work_order', 'author', 'message']
#
#
# @register(Invoice)
# class InvoiceAdmin(SuperuserModelAdmin):
#     list_display = ['vendor', 'remission_address']
