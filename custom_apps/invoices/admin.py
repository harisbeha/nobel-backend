# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models.query_utils import Q
from nested_admin.nested import NestedModelAdmin, NestedStackedInline

from custom_apps.utils import maps
from custom_apps.utils.admin_utils import generate_field_getter
from .enums import ReportState
from .models import Invoice, WorkOrder, Job, Vendor


# actions

def make_state_ticker(path_to_state, from_state, to_state):
    """
    This silly little guy is a factory function which generates an ordinary function to tick the state enum of several
    jobs forward in sync given a queryset of a particular type.

    :param path_to_state:       The path through the model to the state field that needs to be updated, separtaed by
                                "__", e.g. "workorder__job__state"
    :param from_state:          The ResponseState member that all the states must be at in order to validate this tick
    :param to_state:            The ResponseState member to change all the states to
    :return:                    A function to tick a queryset forward:
                                ticker(queryset, success_callback, failure_callback). The callbacks take no args.
    """

    def ticker(queryset, success_callback, failure_callback):
        if list(queryset.values_list(path_to_state, flat=True).distinct()) \
                == [from_state.value]:
            # potential for races here - TODO handle failures in the same transaction as the update?
            queryset.filter(**{path_to_state: from_state.value}) \
                .update(**{path_to_state: to_state.value})
            success_callback()
        else:
            failure_callback()

    return ticker


def make_state_ticker_action(short_description, path_to_state, from_state, to_state, failure_message):
    """
    This silly little guy is a factory function which generates an admin action that can be used to tick the state enum
    of several jobs forward in sync. Since it's an admin action, it will be implicitly associated with a particular
    model.

    :param short_description:   The textual description that should be seen in the actions dropdown
    :param path_to_state:       The path through the model to the state field that needs to be updated, separtaed by
                                "__", e.g. "workorder__job__state"
    :param from_state:          The ResponseState member that all the states must be at in order to validate this tick
    :param to_state:            The ResponseState member to change all the states to
    :param failure_message:     A message to show to the user if the operation fails because not all the jobs are in the
                                right state
    :return:                    A function to tick a queryset forward and call a callback if it fails
    """
    ticker = make_state_ticker(path_to_state, from_state, to_state)

    def admin_action(modeladmin, request, queryset):
        def failure():
            modeladmin.message_user(request, failure_message, level=messages.ERROR)

        ticker(queryset, lambda: None, failure)

    admin_action.short_description = short_description
    return admin_action


def close_safety_review(modeladmin, request, queryset):
    ticker = make_state_ticker(
        'workorder__job__state',
        ReportState.SAFETY_REVIEWED,
        ReportState.SAFETY_REVIEW_CLOSED)

    def failure():
        modeladmin.message_user(
            request,
            "Some of the jobs in the selected invoices have not had their safety reviews approved.",
            level=messages.ERROR)

    def success():
        for invoice in queryset.all():
            Invoice.objects.create(vendor=invoice.vendor, invoice_number=None, remission_address=None)

    if queryset.filter(Q(invoice_number__isnull=True) | Q(remission_address__isnull=True)).count() > 0:
        modeladmin.message_user(
            request,
            "The invoice(s) you've selected don't have their invoice numbers or remission addresses set.",
            level=messages.ERROR)
    elif queryset.filter(Q(workorder__isnull=False)).count() == 0:
        modeladmin.message_user(
            request,
            "There are no work orders attached to this invoice!",
            level=messages.ERROR)
    elif queryset.filter(Q(workorder__job__isnull=True)).count() > 0:
        modeladmin.message_user(
            request,
            "Some of the work orders attached to this invoice have no work done!!!! :(",
            level=messages.ERROR)
    else:
        ticker(queryset, success, failure)


close_safety_review.short_description = 'Close safety reviews'


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
            address = self.cleaned_data[address_field]
            formal_address = maps.formalize_address(address)

            if not formal_address:
                raise ValidationError('Address not found on Google')
            self.cleaned_data[address_field] = formal_address

    return AddressForm


# model admins
class BaseModelAdmin(NestedModelAdmin):
    PERM_CONFIGS = {'Internal Staff': {'perms': ['add', 'change', 'list']}}

    def get_actions(self, request):
        actions = super(BaseModelAdmin, self).get_actions(request)
        if not self._do_check(request, 'delete'):
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def _do_check(self, request, perm_name):
        if request.user.is_superuser:
            return True
        user_perms = request.user.groups.filter(name__in=self.PERM_CONFIGS.keys()).values_list('name', flat=True)
        for perm in user_perms:
            conf = self.PERM_CONFIGS.get(perm, {}).get('perms', [])
            if perm_name in conf:
                return True
        return False

    def has_delete_permission(self, request, obj=None):
        return self._do_check(request, 'delete')

    def has_add_permission(self, request):
        return self._do_check(request, 'add')

    def has_change_permission(self, request, obj=None):
        return self._do_check(request, 'change')

    def has_module_permission(self, request):
        return self._do_check(request, 'list')


class BaseInline(NestedStackedInline):
    extra = 0


class JobInline(BaseInline):
    model = Job


class WorkOrderInline(BaseInline):
    model = WorkOrder
    inlines = [JobInline]
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

    actions = [close_safety_review]


class VendorAdmin(BaseModelAdmin):
    form = address_form_factory(Vendor, ['id'], 'address')

    list_display = ['name', 'address']


class JobAdmin(BaseModelAdmin):
    get_state = generate_field_getter('state', 'Report State', preprocessor=ReportState.human_name)
    get_visit_subtotal = generate_field_getter('visit_subtotal', 'Visit Subtotal')

    actions = [make_state_ticker_action('Approve safety report for selected', 'state', ReportState.INITIALIZED,
                                        ReportState.SAFETY_REVIEWED,
                                        "These jobs are not all in the \"ready to review\" state.")]

    list_display = [get_state, 'work_order', 'response_time_start', 'response_time_end', 'provided_deicing',
                    'provided_plowing', get_visit_subtotal]


class WorkOrderAdmin(BaseModelAdmin):
    get_state = generate_field_getter('state', 'Report State', preprocessor=ReportState.human_name)

    form = address_form_factory(WorkOrder, ['id'], 'building_address')
    list_display = [get_state, 'order_number', 'invoice', 'storm_name', 'building_address']


admin.site.register(Vendor, VendorAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(WorkOrder, WorkOrderAdmin)
admin.site.register(Job, JobAdmin)
