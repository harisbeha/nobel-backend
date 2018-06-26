from django.contrib.admin import register
from import_export.admin import ImportExportActionModelAdmin
from django.shortcuts import HttpResponseRedirect
from django.conf.urls import url
import sendgrid
from sendgrid.helpers.mail import *

from ..resources import *

import nested_admin
from raven import Client
from .helpers import get_locations_by_system_user
from .admin_forms import SafetyReportForm, SRFormSet, WOFormSet
from django.utils.functional import curry
from decimal import *
from django.contrib.admin.utils import flatten_fieldsets

client = Client('https://4d87c7cd417f4e14be43597f3ffac1b3:d46f2a1776a54a8a80d3d8ab57717c71@sentry.io/1219530')


# Start Subinlines
class WorkVisitProxyInline(nested_admin.NestedTabularInline):
    model = WorkVisit
    extra = 1
    readonly_fields = []
    classes = []


class SafetyVisitProxyInline(nested_admin.NestedTabularInline):
    model = SafetyVisit
    extra = 1
    max_num = 1
    classes = []


# Start Inlines

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
        return '${0}'.format(Decimal(obj.aggregate_invoiced_plow_cost) + Decimal(obj.aggregate_invoiced_salt_cost))

    def get_formset(self, *args, **kwargs):
        formset = super(WorkOrderInline, self).get_formset(*args, **kwargs)
        return formset

    def get_formset(self, request, obj=None, **kwargs):
        """
        Pre-populating formset using GET params
        """
        formset = super(WorkOrderInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

    def get_extra(self, request, obj=None, **kwargs):
        """Dynamically sets the number of extra forms. 0 if the related object
        already exists or the extra configuration otherwise."""
        if obj:
            return 0
        return len(get_locations_by_system_user(request.user).values_list('id', flat=True))




# Start ModelAdmins
class SafetyReportAdmin(nested_admin.NestedModelAdmin):
    exclude=['remission_address', 'address_info_storage']
    list_display=['reports', 'status']
    inlines = [SafetyReportInline]
    readonly_fields = ['status', 'dispute_status']
    limited_manytomany_fields = {}
    actions=['rollup_closeout']
    # form = SafetyInvoiceForm

    change_list_template = "admin/provider/safety_report_changelist.html"

    def get_queryset(self, request):
        qs = super(SafetyReportAdmin, self).get_queryset(request)
        prelim = SafetyReportVendor.objects.filter(status__in=['not_created', 'safety_report'],
                                          service_provider__system_user=request.user)
        return prelim

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['service_provider'].queryset = Vendor.objects.filter(system_user=request.user)
        return super(SafetyReportAdmin, self).render_change_form(request, context, args, kwargs)

    def get_changeform_initial_data(self, request):
        vend_id = '{0}'.format(Vendor.objects.get(system_user=request.user).id)
        return {'service_provider': vend_id}

    def reports(self, obj):
        return obj

    def get_urls(self):
        urls = super(SafetyReportAdmin, self).get_urls()
        my_urls = [
            url('generate_closeout/', self.rollup_closeout),
        ]
        return my_urls + urls

    def finalize_safety_report(self, request, queryset):
        rows_updated = queryset.update(status='preliminary_created')
        return HttpResponseRedirect("/provider/invoices/vendorinvoiceproxy/")


    def rollup_closeout(self, request, queryset):
        import random
        from itertools import chain
        combined_list = []
        parent = queryset.first()
        remove = queryset.exclude(id=parent.id)
        work_orders = []
        safety_reports = []
        for inv in remove:
            parent.safetyreport_set.set(inv.safetyreport_set.all())
            inv.delete()
        for safety_report in parent.safetyreport_set.all():
            work_order_code = 'T'.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVXYZ') for i in range(6))
            work_order, wo_created = WorkOrder.objects.get_or_create(building=safety_report.building,
                                            invoice=safety_report.invoice,
                                            work_order_code=work_order_code)
            for safety_visit in safety_report.safetyvisit_set.filter(site_serviced=True):
                workvisit, wv_created = WorkVisit.objects.get_or_create(service_date=safety_visit.inspection_date, work_order_id=work_order.id)
        parent.status = 'preliminary_created'
        parent.save()
        return HttpResponseRedirect("/provider/invoices/invoicevendor/")

    rollup_closeout.short_description = "Generate Closeout Report"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            kwargs["queryset"] = Building.objects.filter(service_provider__system_user=request.user)
        return super(SafetyReportAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)



class PrelimInvoiceAdmin(nested_admin.NestedModelAdmin, ImportExportActionModelAdmin):
    resource_class = VendorInvoiceProxyResource
    exclude=['remission_address', 'address_info_storage']
    list_display=['invoices', 'status']
    readonly_fields = ['status', 'dispute_status']
    inlines = [WorkOrderInline]
    limited_manytomany_fields = {}

    def get_queryset(self, request):
        qs = super(PrelimInvoiceAdmin, self).get_queryset(request)
        prelim = InvoiceVendor.objects.filter(status__in=['preliminary_created', 'submitted'],
                                          service_provider__system_user=request.user)
        return prelim

    actions=['finalize_submit_invoice']

    change_list_template = "admin/provider/safety_report_changelist.html"

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['service_provider'].queryset = Vendor.objects.filter(system_user=request.user)
        return super(PrelimInvoiceAdmin, self).render_change_form(request, context, args, kwargs)

    def get_changeform_initial_data(self, request):
        vend_id = '{0}'.format(Vendor.objects.get(system_user=request.user).id)
        return {'service_provider': vend_id}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            kwargs["queryset"] = Building.objects.filter(service_provider__system_user=request.user)
        return super(PrelimInvoiceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

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
        return HttpResponseRedirect("/provider/invoices/invoicevendor/")

    def get_readonly_fields(self, request, obj=None):
        if obj.status == 'submitted':
            return ['status', 'storm_name', 'storm_date', 'dispute_status']
        else:
            return ['remission_address', 'address_info_storage']

    finalize_submit_invoice.short_description = "Finalize and submit invoice"




