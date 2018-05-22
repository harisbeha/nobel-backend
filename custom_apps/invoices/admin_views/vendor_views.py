from django.contrib.admin import register, ModelAdmin
from import_export.admin import ImportExportActionModelAdmin

from ..models import *
from django.forms.models import BaseModelFormSet

from django.forms.models import BaseInlineFormSet, BaseFormSet
import nested_admin


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
    # print(self.__dict__)
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

def get_locations_by_system_user(user=None):
    # vendor = Vendor.objects.filter(system_user__email='VENDOR@VENDOR.com')[0]
    vend = Vendor.objects.get(system_user__username='vendor-user@bank.com')
    locations = Building.objects.filter(service_provider=vend)
    return locations


class SRFormSet(BaseInlineFormSet):
    model = SafetyReport

    def __init__(self, *args, **kwargs):
        super(SRFormSet, self).__init__(*args, **kwargs)
        self.locations = get_locations_by_system_user(self.request.user)


from django.forms import ModelForm
# class WOrderForm(ModelForm):
#     fields = ['vendor', 'building', 'number_plows', 'number_salts']


class WOFormSet(BaseInlineFormSet):
    model = WorkOrder

    def __init__(self, *args, **kwargs):
        super(WOFormSet, self).__init__(*args, **kwargs)
        self.locations = get_locations_by_system_user(self.request.user)


from django.utils.functional import curry




class WorkVisitProxyInline(nested_admin.NestedTabularInline):
    model = WorkVisit
    extra = 1
    classes = ['collapse']

class WorkOrderInline(nested_admin.NestedTabularInline):
    model = WorkOrder
    formset = WOFormSet
    inlines = [WorkVisitProxyInline]

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
            locations = get_locations_by_system_user(request.user).values('id')
            s_name = None if not obj else obj.storm_name
            s_date = '2017-12-10' if not obj else obj.storm_date
            s_provider = None if not obj else obj.service_provider

            for l in locations:
                print({'building': str(l['id']), 'service_provider': s_provider,
                                'storm_name': s_name,'storm_date': s_date,
                                'last_service_date': '2017-12-09', 'num_plows':0, 'num_salts':0,
                                'failed_service':False, 'work_order_code':'Td1290'})
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
        return get_locations_by_system_user(request.user).count()


class SafetyReportInline(admin.TabularInline):
    model = SafetyReport
    # form = SafetyReportForm
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
            print(locations.count())
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


@register(InvoiceProxyVendor)
class InvoiceAdmin(admin.ModelAdmin):
    exclude=['remission_address', 'address_info_storage']
    inlines = [SafetyReportInline]
    limited_manytomany_fields = {}

    def get_changeform_initial_data(self, request):
        """
        Get the initial form data from the request's GET params.
        """
        from django.db import models
        initial_o = Invoice().__dict__
        initial = initial_o
        for k in initial:
            try:
                f = self.model._meta.get_field(k)
            except Exception as e:
                continue
            # We have to special-case M2Ms as a list of comma-separated PKs.
            if isinstance(f, models.ManyToManyField):
                initial[k] = initial[k].split(",")
        else:
            from django.db import models
            initial_o = Invoice().__dict__
            initial = initial_o
            for k in initial:
                try:
                    f = self.model._meta.get_field(k)
                except Exception as e:
                    continue
                # We have to special-case M2Ms as a list of comma-separated PKs.
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")


class PrelimInvoiceAdmin(nested_admin.NestedModelAdmin):
    exclude=['remission_address', 'address_info_storage']
    inlines = [WorkOrderInline]
    readonly_fields = ['status']
    limited_manytomany_fields = {}

    def get_changeform_initial_data(self, request):
        """
        Get the initial form data from the request's GET params.
        """
        from django.db import models
        initial_o = Invoice().__dict__
        initial = initial_o
        for k in initial:
            try:
                f = self.model._meta.get_field(k)
            except Exception as e:
                continue
            # We have to special-case M2Ms as a list of comma-separated PKs.
            if isinstance(f, models.ManyToManyField):
                initial[k] = initial[k].split(",")
        else:
            from django.db import models
            initial_o = Invoice().__dict__
            initial = initial_o
            for k in initial:
                try:
                    f = self.model._meta.get_field(k)
                except Exception as e:
                    continue
                # We have to special-case M2Ms as a list of comma-separated PKs.
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")


# @register(Invoice)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = Invoice
#     list_display = ['storm_name','storm_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [SafetyReportInline]


# @register(InvoiceProxyVendor)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = InvoiceProxyVendor
#     list_display = ['storm_name','storm_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [SafetyReportInline]
#     # change_form_template = 'admin/invoice_admin.html'


# @register(InvoiceProxyPrelim)
# class InvoiceAdmin(admin.ModelAdmin):
#     model = InvoiceProxyPrelim
#     list_display = ['storm_name','storm_date']
#     exclude = ['remission_address', 'address_info_storage']
#     inlines = [WorkOrderInline]
#     change_form_template = 'admin/invoice_admin.html'


# @register(InvoiceProxyForecast)
# class InvoiceForecastAdmin(admin.ModelAdmin):
#
#     pass

class ServiceForecast(admin.ModelAdmin):
    model = WorkProxyServiceForecast
    list_filter = ('invoice_id', 'invoice__storm_name', 'invoice__storm_date')
    list_display = [work_order, invoice, service_provider, location, deicing_rate, deicing_tax, plow_rate,
                    plow_tax, snowfall, storm_days, refreeze,
                    number_salts, number_plows, deicing_fee, plow_fee, storm_total]


class DiscrepancyReview(admin.ModelAdmin):
    model = WorkProxyServiceDiscrepancy
    list_filter = ('invoice_id', 'invoice__storm_name', 'invoice__storm_date')
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


@register(Building)
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


def storm_date(obj):
    return obj.invoice.storm_date


def storm_name(obj):
    return obj.invoice.storm_name

# @register(SafetyReport)
# class SafetyReportAdmin(admin.ModelAdmin):
#     # list_filter = (storm_date, storm_date)
#     list_display = ['building', storm_name, storm_date, 'existing_work_order', 'site_serviced', 'safe_to_open', 'service_time']
#
#     def existing_work_order(self, obj):
#         existing_work_order = WorkOrder.objects.filter(invoice=obj.invoice, building=obj.building).exists()
#         return existing_work_order
#     existing_work_order.boolean = True


# @register(ModifiablePrelimInvoice)
# class ModifyPrelimInvoiceAdmin(admin.ModelAdmin):
#     # list_filter = (storm_date, storm_date)
#     list_filter = ['invoice_id', 'invoice__storm_name', 'invoice__storm_date', 'failed_service']
#     list_editable = ['building', 'last_service_date', 'num_plows', 'num_salts', 'failed_service']
#     list_display = ['id', 'building', service_provider, storm_name, storm_date, 'last_service_date',
#                     'num_plows', 'num_salts', 'failed_service']


#
#
# @register(DiscrepancyReport)
# class DiscrepancyReportAdmin(SuperuserModelAdmin):
#     list_display = ['work_order', 'author', 'message']
#
#
# @register(Invoice)
# class InvoiceAdmin(SuperuserModelAdmin):
#     list_display = ['vendor', 'remission_address']
