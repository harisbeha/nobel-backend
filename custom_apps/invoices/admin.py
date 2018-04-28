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
from custom_apps.utils import maps
from custom_apps.utils.admin_utils import generate_field_getter
from custom_apps.utils.forecast import forecast
from .enums import ReportState
from .models import Invoice, WorkOrder, WorkVisit, SafetyReport, Vendor, VendorSettings


# actions

# def close_safety_review(modeladmin, request, queryset):
#     ticker = make_state_ticker(
#         Invoice,
#         ReportState.SAFETY_REVIEWED,
#         ReportState.SAFETY_REVIEW_CLOSED)
#
#     def failure():
#         modeladmin.message_user(
#             request,
#             "Some of the jobs in the selected invoices have not had their safety reviews approved or are already closed.",
#             level=messages.ERROR)
#
#     def success():
#         for invoice in queryset.all():
#             Invoice.objects.create(vendor=invoice.vendor, invoice_number=None, remission_address=None)
#
#     if queryset.filter(Q(invoice_number__isnull=True) | Q(remission_address__isnull=True)).count() > 0:
#         modeladmin.message_user(
#             request,
#             "The invoice(s) you've selected don't have their invoice numbers or remission addresses set.",
#             level=messages.ERROR)
#     elif queryset.filter(Q(workorder__isnull=False)).count() == 0:
#         modeladmin.message_user(
#             request,
#             "There are no work orders attached to some of these invoices!",
#             level=messages.ERROR)
#     elif queryset.filter(Q(workorder__work__isnull=True)).count() > 0:
#         modeladmin.message_user(
#             request,
#             "Some of the work orders attached to these invoices have no work done!!!! :(",
#             level=messages.ERROR)
#     else:
#         ticker(queryset, success, failure)
#
#
# close_safety_review.short_description = 'Close safety reviews'


# forms

def address_form_factory(model_cls, exclude_list, address_field):
    """
    :(
    """

    class AddressForm(forms.ModelForm):
        class Meta:
            model = model_cls
            exclude = exclude_list

        def clean(self):
            if address_field in self.cleaned_data:
                address = self.cleaned_data[address_field]
                formal_address, details = maps.formalize_address(address)

                if not formal_address:
                    raise ValidationError('Address not found on Google')
                self.cleaned_data[address_field] = formal_address
                self.cleaned_data['address_info_storage'] = details
            return super(AddressForm, self).clean()

    return AddressForm


# model admins
class BaseModelAdmin(NestedModelAdmin):
    """
    This terrible class allows control of module and field visibility based on user groups.
    PERM_CONFIGS allows configuration of the behaviors.
    """
    PERM_CONFIGS = {'Internal Staff':
        {
            'perms': ['add', 'change', 'list'],
            'hidden_fields': {id(WorkOrder): ['plow_tax']},
            'actions': [],
        }
    }

    def get_perm_configs(self, request):
        return self.PERM_CONFIGS

    def _do_check(self, request, perm_name):
        """
        Uses the current user's groups and get_perm_configs to determine if the user has the given named permission on
        this ModelAdmin
        """
        if request.user.is_superuser:
            return True
        perm_configs = self.get_perm_configs(request)
        user_perms = request.user.groups.filter(name__in=perm_configs.keys()).values_list('name', flat=True)
        for perm in user_perms:
            conf = perm_configs.get(perm, {}).get('perms', [])
            if perm_name in conf:
                return True
        return False

    def _get_hidden_fields(self, request, model):
        """
        Use get_perm_configs to get a list of hidden fields for the model
        """
        perm_configs = self.get_perm_configs(request)
        if request.user.is_superuser:
            if settings.DEBUG:
                return perm_configs.get('Internal Staff', {}).get('hidden_fields', {}).get(id(model), [])
            return []
        # TODO handle clashes with multiple groups
        user_perms = request.user.groups.filter(name__in=perm_configs.keys()).values_list('name', flat=True)
        for perm in user_perms:
            return perm_configs.get(perm, {}).get('hidden_fields', {}).get(id(model), [])
        return []

    def _scrub_fields(self, request, formset):
        """
        Uses _get_hidden_fields to replace widgets in the formset with HiddenInput
        """
        model = None
        try:
            model = formset.model
        except:
            try:
                model = formset.model_admin.model
            except:
                pass
        if not model:
            return formset
        hidden_fields = self._get_hidden_fields(request, model)
        for h in hidden_fields:
            if h in formset.form.base_fields:
                formset.form.base_fields[h].widget = HiddenInput()
        return formset

    # EXPORTS START HERE

    def has_delete_permission(self, request, obj=None):
        """
        Uses _do_check to determine if the user should be allowed to delete elements in the list
        """
        return self._do_check(request, 'delete')

    def has_add_permission(self, request):
        """
        Uses _do_check to determine if the user should be allowed to create elements in the list
        """
        return self._do_check(request, 'add')

    def has_change_permission(self, request, obj=None):
        """
        Uses _do_check to determine if the user should be allowed to edit elements in the list
        """
        return self._do_check(request, 'change')

    def has_module_permission(self, request):
        """
        Uses _do_check to determine if the user should be allowed to view the list
        """
        return self._do_check(request, 'list')

    def get_actions(self, request):
        """
        Uses _do_check to filter the actions the user should see (currently just the delete action)
        """
        actions = super(BaseModelAdmin, self).get_actions(request)
        if not self._do_check(request, 'delete'):
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def get_formsets_with_inlines(self, request, obj=None):
        """
        Uses _scrub_fields to filter hidden fields in the formset
        """
        formsets = list(super(BaseModelAdmin, self).get_formsets_with_inlines(request, obj=obj))
        for formset, inline in formsets:
            self._scrub_fields(request, formset)
            yield formset, inline

    def get_changelist_formset(self, request, **kwargs):
        """
        Uses _scrub_fields to filter hidden fields in the formset
        """
        r = super(BaseModelAdmin, self).get_changelist_formset(request, **kwargs)
        return self._scrub_fields(request, r)

    def get_inline_formsets(self, request, formsets, inline_instances,
                            obj=None, allow_nested=False):
        """
        Uses _scrub_fields to filter hidden fields in the formset
        """
        r = super(BaseModelAdmin, self).get_inline_formsets(request, formsets, inline_instances, obj=obj,
                                                            allow_nested=allow_nested)
        return [self._scrub_fields(request, i) for i in r]

    def get_fields(self, request, obj=None):
        """
        Clears the address_info_storage field from the list of fields
        """
        r = super(BaseModelAdmin, self).get_fields(request, obj=obj)
        try:
            r.remove('address_info_storage')
        except ValueError:
            pass
        return r


class BaseInline(NestedStackedInline):
    extra = 0


class SafetyReportInline(BaseInline):
    model = SafetyReport


class WorkOrderInline(BaseInline):
    model = WorkOrder
    inlines = [SafetyReportInline]
    form = address_form_factory(WorkOrder, ['id'], 'building_address')


class InvoiceAdmin(BaseModelAdmin):
    get_vendor_name = generate_field_getter('vendor.name', 'Vendor Name')
    get_vendor_address = generate_field_getter('vendor.address', 'Vendor Address')
    get_state = generate_field_getter('state', 'Report State', preprocessor=ReportState.human_name)

    list_display = [get_state, get_vendor_name, get_vendor_address, 'invoice_number', 'remission_address']

    search_fields = ['vendor__name', 'invoice_number']
    list_filter = ['vendor__name']
    inlines = [WorkOrderInline]
    form = address_form_factory(Invoice, ['id'], 'remission_address')

    # actions = [close_safety_review]


class VendorSettingsInline(NestedStackedInline):
    model = VendorSettings
    min_num = 1
    max_num = 1

    def has_delete_permission(self, request, obj=None):
        return False


class VendorAdmin(BaseModelAdmin):
    form = address_form_factory(Vendor, ['id'], 'address')

    list_display = ['name', 'address', 'system_user', 'region']

    inlines = [VendorSettingsInline]


def get_available_job_options(state, group):
    state_specific_opts = WORKFLOW_SPEC['spec'][state]
    all_perms = ['create', 'edit']
    all_actions = ['send', 'close']
    allowed_items = state_specific_opts['allowed'][group]
    available_actions = [i for i in allowed_items.get('actions', []) if i in all_actions]
    available_perms = ['list'] + [i for i in allowed_items.get('perms', []) if i in all_perms]
    return {group: {'perms': available_perms, 'hidden_fields': [], 'actions': available_actions}}


# class JobAdmin(BaseModelAdmin):
#     FOR_WORKFLOW_STATE = ReportState.CREATED
#     def get_perm_configs(self, request):
#         group = request.user.groups.first()
#         return get_available_job_options(group, self.FOR_WORKFLOW_STATE)
#     get_state = generate_field_getter('state', 'Report State', preprocessor=ReportState.human_name)
#     get_visit_subtotal = generate_field_getter('visit_subtotal', 'Visit Subtotal')
#
#     actions = [make_state_ticker_action('Approve safety report for selected', SafetyReport, ReportState.INITIALIZED,
#                                         ReportState.SAFETY_REVIEWED,
#                                         "These jobs are not all in the \"ready to review\" state.")]
#
#     list_display = [get_state, 'work_order', 'response_time_start', 'response_time_end', 'provided_deicing',
#                     'provided_plowing', get_visit_subtotal]
#
#     exclude = ['state']


class WorkOrderForm(address_form_factory(WorkOrder, ['id'], 'building_address')):
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.all())

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance', None):
            self.base_fields['vendor'].initial = kwargs['instance'].invoice.vendor
        super(WorkOrderForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.cleaned_data.get('vendor', None):
            self.cleaned_data['invoice'] = Invoice.objects.filter(vendor=self.cleaned_data['vendor']).order_by(
                '-created').first()
            # del r['vendor']
            # do we want this? if we delete the property the user might have to reinput it if validation fails
            # if we don't delete it it might mess up the db operation?
            # ?????????
        return super(WorkOrderForm, self).clean()

class SafetyReportAdmin(BaseModelAdmin):
    # form = address_form_factory(Vendor, ['id'], 'address')

    list_display = ['safe_to_open', 'safety_concerns', 'snow_instructions', 'haul_stack_status', 'haul_stack_estimate']


class WorkOrderAdmin(BaseModelAdmin):
    get_state = generate_field_getter('state', 'Report State', preprocessor=ReportState.human_name)

    form = WorkOrderForm
    list_display = [get_state, 'order_number', 'invoice', 'storm_name', 'building_address']

    def get_form(self, request, obj=None, **kwargs):
        r = super(WorkOrderAdmin, self).get_form(request, obj=obj, **kwargs)
        r.base_fields['invoice'].widget = forms.HiddenInput()
        return r


class VendorSettingsAdmin(BaseModelAdmin):
    list_display = ['const_a', 'const_b']


def extract_goodies_from_workorder(obj):
    return (11111, obj.last_service_time, obj.work_end)


def get_bq_data(obj):
    return query_for_accumulation_zip(*extract_goodies_from_workorder(obj))


def get_magic_data(obj):
    bq_data = get_bq_data(obj)
    return forecast(obj.invoice.vendor.settings, bq_data['snowfall'], bq_data['duration'], bq_data['has_ice'])


def get_snowfall(obj):
    return get_bq_data(obj)['snowfall']


get_snowfall.short_description = 'inches of snowfall'
get_snowfall.admin_order_field = ''


def get_ice(obj):
    return get_bq_data(obj)['has_ice']


get_ice.short_description = 'ice?'
get_ice.admin_order_field = ''


def get_storm_length(obj):
    return get_bq_data(obj)['snowfall']


get_storm_length.short_description = 'days of storm'
get_storm_length.admin_order_field = ''


def get_num_plows(obj):
    return get_magic_data(obj)['plows']


get_num_plows.short_description = 'projected no. plows'
get_num_plows.admin_order_field = ''


def get_num_salts(obj):
    return get_magic_data(obj)['salts']


get_num_salts.short_description = 'projected no. salts'
get_num_salts.admin_order_field = ''


def get_num_jobs(obj):
    return SafetyReport.objects.filter(work_order=obj).count()


get_num_jobs.short_description = 'no. visits'
get_num_jobs.admin_order_field = ''


def get_workorder_cost(obj):
    return SafetyReport.objects.filter(work_order=obj).aggregate(Sum('visit_subtotal'))


get_workorder_cost.description = 'work order subtotal'
get_workorder_cost.admin_order_field = ''


class WorkOrderWeatherReviewAdmin(BaseModelAdmin):
    list_display = ['order_number',
                    generate_field_getter('invoice.vendor.name', 'Vendor'),
                    'storm_name',
                    'building_id',
                    'building_address',
                    get_num_jobs,
                    get_workorder_cost,
                    get_storm_length,
                    get_snowfall,
                    get_ice,
                    get_num_plows,
                    get_num_salts]


#admin.site.register(Vendor, VendorAdmin)
#admin.site.register(Invoice, InvoiceAdmin)
#admin.site.register(WorkOrder, WorkOrderAdmin)
#admin.site.register(Job, JobAdmin)
#admin.site.register(VendorSettings, VendorSettingsAdmin)
#admin.site.register(WorkOrderProxyWeatherReview, WorkOrderWeatherReviewAdmin)

from .admin_views import superuser_views, nwa_views, cbre_views, vendor_views
